"""Syncs one mail folder through its messages delta; the cursor is the folder's delta link.

A full load asks for the messages received since SYNC_FROM. Graph caps such a filtered load at
5,000 messages, so a folder that reaches the cap is loaded again without the filter (older
messages are then left out here). Pages are committed one by one, and the delta link is saved only
once the folder's round has completed, so an interrupted run repeats it (re-saving is a no-op).
"""

import logging
from dataclasses import dataclass, field

from bubble_core.log import get_logger
from bubble_core.sync_cursors import load_cursor, save_cursor
from bubble_ingest.l0_sync import CursorExpired
from bubble_ingest.microsoft.mail import api
from bubble_ingest.microsoft.mail.mapping import SOURCE
from bubble_ingest.microsoft.mail.scope import RECEIVED_FILTER
from bubble_ingest.microsoft.mail.store import Mailbox, flag_missing, save_page

logger = get_logger(__name__)


@dataclass
class _Round:
    """What one round of a folder's delta returned and changed."""

    full_load: bool
    fetched: int = 0
    changed: int = 0
    seen_ids: set[str] = field(default_factory=set)
    delta_link: str | None = None


def sync_folder(mailbox: Mailbox, folder_id: str) -> None:
    """Apply the folder's changes since its delta link, or load it fully when none or expired."""
    cursor = load_cursor(mailbox.conn, mailbox.account.id, SOURCE, folder_id)
    if cursor:
        try:
            _finish(mailbox, folder_id, _run_round(mailbox, folder_id, cursor, None))
            return
        except CursorExpired:
            logger.warning("Delta link of folder %s expired; loading it fully", folder_id)
    _finish(mailbox, folder_id, _load_fully(mailbox, folder_id))


def _load_fully(mailbox: Mailbox, folder_id: str) -> _Round:
    logger.info("Folder %s: full load", folder_id)
    result = _run_round(mailbox, folder_id, None, RECEIVED_FILTER)
    if result.fetched >= api.FILTER_CAP:
        logger.info("Folder %s reached the filter cap; loading it unfiltered", folder_id)
        result = _run_round(mailbox, folder_id, None, None)
    result.changed += flag_missing(mailbox, folder_id, result.seen_ids)
    return result


def _run_round(
    mailbox: Mailbox, folder_id: str, delta_link: str | None, received_filter: str | None
) -> _Round:
    """Fetch and save the folder's delta page by page, each page committed."""
    result = _Round(full_load=delta_link is None)
    pages = api.iter_message_pages(mailbox.session, folder_id, delta_link, received_filter)
    for page in pages:
        saved = save_page(mailbox, folder_id, page.entries)
        result.fetched += len(page.entries)
        result.changed += saved.changed
        result.seen_ids |= saved.message_ids
        result.delta_link = page.delta_link or result.delta_link
        if result.full_load:
            logger.info("Folder %s: %d messages loaded", folder_id, result.fetched)
    return result


def _finish(mailbox: Mailbox, folder_id: str, result: _Round) -> None:
    """Store the next delta link, committed together with a full load's deletion flags."""
    if not result.delta_link:
        raise RuntimeError(f"Graph returned no delta link for folder {folder_id}")
    save_cursor(mailbox.conn, mailbox.account.id, SOURCE, folder_id, result.delta_link)
    mailbox.conn.commit()
    logger.log(
        logging.INFO if result.fetched else logging.DEBUG,
        "%s folder %s: %d fetched, %d changed (%s)",
        SOURCE,
        folder_id,
        result.fetched,
        result.changed,
        "full load" if result.full_load else "incremental",
    )

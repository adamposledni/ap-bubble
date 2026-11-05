"""Writes one account's messages into L0, batch by batch, each batch committed on its own.

Fetching a batch before writing it keeps the write transaction short, so other jobs sharing
the vault are not locked out while Gmail's quota slows the fetching down.
"""

import sqlite3
from dataclasses import dataclass

from google.auth.transport.requests import AuthorizedSession

from bubble_core.accounts import Account
from bubble_core.items import flag_deleted, save_item
from bubble_core.job_log import JobRun
from bubble_core.log import get_logger
from bubble_ingest.google.gmail import api
from bubble_ingest.google.gmail.mapping import CONTAINER_ID, SOURCE, to_item
from bubble_ingest.google.gmail.scope import in_scope
from bubble_ingest.google.http import Json

BATCH_SIZE = 100  # about a minute of Gmail quota

logger = get_logger(__name__)


@dataclass(frozen=True)
class Mailbox:
    """One account's mailbox being synced: read through session, written through conn."""

    conn: sqlite3.Connection
    session: AuthorizedSession
    account: Account
    run: JobRun


def save_messages(mailbox: Mailbox, message_ids: list[str]) -> int:
    """Fetch and save the messages; return how many rows really changed.

    Messages gone from Gmail or out of scope (e.g. moved to trash) only flag known rows.
    """
    changed = 0
    for start in range(0, len(message_ids), BATCH_SIZE):
        batch = message_ids[start : start + BATCH_SIZE]
        fetched = {message_id: api.get_message(mailbox.session, message_id) for message_id in batch}
        changed += _save_batch(mailbox, fetched)
        mailbox.conn.commit()
        mailbox.run.items_processed += len(batch)
        logger.info("Saved %d of %d messages", start + len(batch), len(message_ids))
    return changed


def flag_gone(mailbox: Mailbox, message_ids: list[str]) -> int:
    """Flag known messages as deleted; callers commit."""
    account_id, run_id = mailbox.account.id, mailbox.run.id
    return flag_deleted(mailbox.conn, account_id, SOURCE, CONTAINER_ID, message_ids, run_id)


def _save_batch(mailbox: Mailbox, fetched: dict[str, Json | None]) -> int:
    kept = [m for m in fetched.values() if m is not None and in_scope(m)]
    kept_ids = {message["id"] for message in kept}
    gone = [message_id for message_id in fetched if message_id not in kept_ids]
    account_id, run_id = mailbox.account.id, mailbox.run.id
    saved = sum(save_item(mailbox.conn, account_id, to_item(m), run_id) for m in kept)
    flagged = flag_gone(mailbox, gone)
    logger.debug("Batch of %d: %d saved, %d flagged deleted", len(fetched), saved, flagged)
    return saved + flagged

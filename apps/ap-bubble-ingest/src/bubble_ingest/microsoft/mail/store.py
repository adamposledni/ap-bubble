"""Writes Outlook mail into L0, one folder per container, each page of changes committed on its own.

A message lives in one folder and keeps its (immutable) id when moved. Saving it in a folder
therefore flags its live row in any other folder, so a move never leaves two live rows: not between
the two folders' syncs, nor when the old folder's sync fails. The old folder's @removed entry then
finds nothing left to flag.
"""

import sqlite3
from collections import defaultdict
from dataclasses import dataclass

import requests

from bubble_core.accounts import Account
from bubble_core.items import flag_deleted, flag_missing_deleted, save_item
from bubble_core.job_log import JobRun
from bubble_core.log import get_logger
from bubble_core.sync_cursors import save_cursor
from bubble_ingest.l0_sync import CONTAINER_LIST_ID
from bubble_ingest.microsoft.graph import Json
from bubble_ingest.microsoft.mail.mapping import SOURCE, is_removed, to_item
from bubble_ingest.microsoft.mail.scope import in_scope

_RESET_CURSOR = ""  # falsy, so the folder's next sync is a full load

logger = get_logger(__name__)


@dataclass(frozen=True)
class Mailbox:
    """One account's mailbox being synced: read through session, written through conn."""

    conn: sqlite3.Connection
    session: requests.Session
    account: Account
    run: JobRun


@dataclass(frozen=True)
class SavedPage:
    message_ids: set[str]  # messages saved: in scope and not removed
    changed: int  # rows really changed


def save_page(mailbox: Mailbox, folder_id: str, entries: list[Json]) -> SavedPage:
    """Save a page of a folder's delta: changed messages, removals and moves away; commit.

    Out-of-scope messages are left out; removals only flag known rows.
    """
    conn, account_id, run_id = mailbox.conn, mailbox.account.id, mailbox.run.id
    removed = [entry["id"] for entry in entries if is_removed(entry)]
    messages = [entry for entry in entries if not is_removed(entry) and in_scope(entry)]
    ids = {message["id"] for message in messages}
    changed = sum(save_item(conn, account_id, to_item(folder_id, m), run_id) for m in messages)
    changed += flag_deleted(conn, account_id, SOURCE, folder_id, removed, run_id)
    changed += _flag_moved_away(mailbox, folder_id, ids)
    conn.commit()
    mailbox.run.items_processed += len(entries)
    logger.debug(
        "Folder %s: page of %d, %d saved, %d removed, %d changed",
        folder_id,
        len(entries),
        len(ids),
        len(removed),
        changed,
    )
    return SavedPage(ids, changed)


def flag_missing(mailbox: Mailbox, folder_id: str, seen_ids: set[str]) -> int:
    """After a full load: flag the folder's messages it no longer returned; callers commit."""
    account_id, run_id = mailbox.account.id, mailbox.run.id
    return flag_missing_deleted(mailbox.conn, account_id, SOURCE, folder_id, seen_ids, run_id)


def retire_vanished_folders(mailbox: Mailbox, folder_ids: set[str]) -> None:
    """Flag the messages of folders no longer synced (deleted, or moved below a skipped folder).

    Their cursor is reset, so a folder that comes back (e.g. restored) is loaded fully again.
    """
    conn, account_id, run_id = mailbox.conn, mailbox.account.id, mailbox.run.id
    rows = conn.execute(
        "SELECT DISTINCT container_id FROM l0_items "
        "WHERE account_id = ? AND source = ? AND container_id != ? AND deleted = 0",
        (account_id, SOURCE, CONTAINER_LIST_ID),
    ).fetchall()
    for folder_id in {row["container_id"] for row in rows} - folder_ids:
        flagged = flag_missing_deleted(conn, account_id, SOURCE, folder_id, set(), run_id)
        save_cursor(conn, account_id, SOURCE, folder_id, _RESET_CURSOR)
        logger.info(
            "Folder %s is no longer synced; %d messages flagged deleted", folder_id, flagged
        )
    conn.commit()


def _flag_moved_away(mailbox: Mailbox, folder_id: str, message_ids: set[str]) -> int:
    """Flag live rows of these messages in other folders: the messages moved here from there."""
    if not message_ids:
        return 0
    conn, account_id, run_id = mailbox.conn, mailbox.account.id, mailbox.run.id
    marks = ",".join("?" * len(message_ids))
    rows = conn.execute(
        "SELECT container_id, external_id FROM l0_items WHERE account_id = ? AND source = ? "
        f"AND deleted = 0 AND container_id NOT IN (?, ?) AND external_id IN ({marks})",
        (account_id, SOURCE, folder_id, CONTAINER_LIST_ID, *message_ids),
    ).fetchall()
    moved: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        moved[row["container_id"]].append(row["external_id"])
    for old_folder_id, ids in moved.items():
        logger.debug("%d messages moved from folder %s to %s", len(ids), old_folder_id, folder_id)
    return sum(
        flag_deleted(conn, account_id, SOURCE, old_folder_id, ids, run_id)
        for old_folder_id, ids in moved.items()
    )

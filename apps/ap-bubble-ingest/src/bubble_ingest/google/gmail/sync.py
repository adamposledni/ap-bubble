"""Ingest job: syncs the mailbox of every Google account into L0 (one container per account).

The cursor is Gmail's history id. A full load lists the messages in scope; later runs apply
the history since the cursor. The cursor is saved only once a load or a sync has completed,
so an interrupted run is repeated from the same cursor (saving the same message twice is a no-op).
"""

import sqlite3

from bubble_core.accounts import Account
from bubble_core.items import flag_missing_deleted
from bubble_core.job_log import job_run
from bubble_core.log import get_logger
from bubble_core.sync_cursors import load_cursor, save_cursor
from bubble_ingest.google import auth as google_auth
from bubble_ingest.google.gmail import api
from bubble_ingest.google.gmail.history import message_changes
from bubble_ingest.google.gmail.mapping import CONTAINER_ID, SOURCE
from bubble_ingest.google.gmail.scope import LIST_QUERY
from bubble_ingest.google.gmail.store import Mailbox, flag_gone, save_messages
from bubble_ingest.l0_sync import CursorExpired, sync_accounts

JOB_NAME = f"ingest.{SOURCE}"

logger = get_logger(__name__)


def sync_all(conn: sqlite3.Connection) -> None:
    sync_accounts(conn, "google", sync_account)


def sync_account(conn: sqlite3.Connection, account: Account) -> None:
    with job_run(conn, JOB_NAME, account.key) as run:
        mailbox = Mailbox(conn, google_auth.session_for(account.key), account, run)
        history_id = _sync(mailbox)
        save_cursor(conn, account.id, SOURCE, CONTAINER_ID, history_id)
        conn.commit()


def _sync(mailbox: Mailbox) -> str:
    """Apply the changes since the stored cursor, or load fully; return the next cursor."""
    cursor = load_cursor(mailbox.conn, mailbox.account.id, SOURCE, CONTAINER_ID)
    if cursor:
        try:
            return _apply_history(mailbox, cursor)
        except CursorExpired:
            logger.warning("Gmail history of %s expired; loading fully", mailbox.account.key)
    return _load_fully(mailbox)


def _load_fully(mailbox: Mailbox) -> str:
    # Read before listing: whatever changes during the load is in the history after it.
    history_id = api.current_history_id(mailbox.session)
    message_ids = api.list_message_ids(mailbox.session, LIST_QUERY)
    changed = save_messages(mailbox, message_ids)
    account, run_id = mailbox.account, mailbox.run.id
    seen = set(message_ids)
    changed += flag_missing_deleted(mailbox.conn, account.id, SOURCE, CONTAINER_ID, seen, run_id)
    logger.info("Gmail %s: full load, %d messages, %d changed", account.key, len(seen), changed)
    return history_id


def _apply_history(mailbox: Mailbox, cursor: str) -> str:
    history = api.list_history(mailbox.session, cursor)
    changes = message_changes(history.records)
    flagged = flag_gone(mailbox, changes.deleted_ids)
    mailbox.conn.commit()
    changed = flagged + save_messages(mailbox, changes.changed_ids)
    logger.info(
        "Gmail %s: incremental, %d deleted, %d to fetch, %d changed",
        mailbox.account.key,
        len(changes.deleted_ids),
        len(changes.changed_ids),
        changed,
    )
    return history.history_id

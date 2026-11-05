"""Ingest job: syncs every readable calendar of every Google account into L0."""

import sqlite3

from google.auth.transport.requests import AuthorizedSession

from bubble_core.accounts import Account, list_accounts
from bubble_core.items import flag_missing_deleted, save_item
from bubble_core.job_log import JobRun, job_run
from bubble_core.log import get_logger
from bubble_core.sync_cursors import load_cursor, save_cursor
from bubble_ingest.google import auth as google_auth
from bubble_ingest.google.calendar import api
from bubble_ingest.google.calendar.mapping import SOURCE, to_item

JOB_NAME = f"ingest.{SOURCE}"
SYNC_FROM = "2026-01-01T00:00:00Z"  # older history is not loaded yet, see other/TODO.md
_READABLE_ROLES = {"owner", "writer", "reader"}  # freeBusyReader gives no event details

logger = get_logger(__name__)


def sync_all(conn: sqlite3.Connection) -> None:
    """Sync every enabled Google account; a failed account does not stop the others."""
    failed = []
    for account in list_accounts(conn, "google"):
        try:
            sync_account(conn, account)
        except Exception:  # already logged and recorded by job_run
            failed.append(account.key)
    if failed:
        raise RuntimeError(f"Calendar sync failed for {failed}")


def sync_account(conn: sqlite3.Connection, account: Account) -> None:
    with job_run(conn, JOB_NAME, account.key) as run:
        session = google_auth.session_for(account.key)
        for calendar in _readable_calendars(session):
            _sync_calendar(conn, session, account, calendar["id"], run)


def _readable_calendars(session: AuthorizedSession) -> list[api.Json]:
    calendars = api.list_calendars(session)
    readable = [c for c in calendars if c.get("accessRole") in _READABLE_ROLES]
    logger.debug("%d of %d calendars are readable", len(readable), len(calendars))
    return readable


def _sync_calendar(
    conn: sqlite3.Connection,
    session: AuthorizedSession,
    account: Account,
    calendar_id: str,
    run: JobRun,
) -> None:
    """Save one calendar's changes and commit them together with its new cursor."""
    changes, full_load = _fetch(conn, session, account, calendar_id)
    changed = sum(
        save_item(conn, account.id, to_item(calendar_id, event), run.id) for event in changes.events
    )
    if full_load:
        seen = {event["id"] for event in changes.events}
        changed += flag_missing_deleted(conn, account.id, SOURCE, calendar_id, seen, run.id)
    save_cursor(conn, account.id, SOURCE, calendar_id, changes.next_sync_token)
    conn.commit()
    run.items_processed += len(changes.events)
    logger.info(
        "Calendar %s: %d events fetched, %d changed (%s)",
        calendar_id,
        len(changes.events),
        changed,
        "full load" if full_load else "incremental",
    )


def _fetch(
    conn: sqlite3.Connection, session: AuthorizedSession, account: Account, calendar_id: str
) -> tuple[api.EventChanges, bool]:
    """Changes since the stored cursor; a full load when there is none or it expired."""
    token = load_cursor(conn, account.id, SOURCE, calendar_id)
    if token:
        try:
            return api.list_events(session, calendar_id, token, SYNC_FROM), False
        except api.SyncTokenExpired:
            logger.warning("Sync token of calendar %s expired; loading it fully", calendar_id)
    return api.list_events(session, calendar_id, None, SYNC_FROM), True

"""Ingest job: syncs every readable calendar of every Google account into L0."""

import sqlite3
from functools import partial

from google.auth.transport.requests import AuthorizedSession

from bubble_core.accounts import Account
from bubble_core.job_log import job_run
from bubble_core.log import get_logger
from bubble_ingest.google import auth as google_auth
from bubble_ingest.google.calendar import api
from bubble_ingest.google.calendar.mapping import SOURCE, to_item
from bubble_ingest.google.http import Json
from bubble_ingest.l0_sync import ContainerChanges, sync_accounts, sync_container

JOB_NAME = f"ingest.{SOURCE}"
SYNC_FROM = "2026-01-01T00:00:00Z"  # older history is not loaded yet, see other/TODO.md
_READABLE_ROLES = {"owner", "writer", "reader"}  # freeBusyReader gives no event details

logger = get_logger(__name__)


def sync_all(conn: sqlite3.Connection) -> None:
    sync_accounts(conn, "google", sync_account)


def sync_account(conn: sqlite3.Connection, account: Account) -> None:
    with job_run(conn, JOB_NAME, account.key) as run:
        session = google_auth.session_for(account.key)
        for calendar in _readable_calendars(session):
            fetch = partial(_fetch_changes, session, calendar["id"])
            sync_container(conn, account, SOURCE, calendar["id"], fetch, run)


def _readable_calendars(session: AuthorizedSession) -> list[Json]:
    calendars = api.list_calendars(session)
    readable = [c for c in calendars if c.get("accessRole") in _READABLE_ROLES]
    logger.debug("%d of %d calendars are readable", len(readable), len(calendars))
    return readable


def _fetch_changes(
    session: AuthorizedSession, calendar_id: str, sync_token: str | None
) -> ContainerChanges:
    result = api.list_events(session, calendar_id, sync_token, SYNC_FROM)
    items = [to_item(calendar_id, event) for event in result.events]
    return ContainerChanges(items, result.next_sync_token, full_load=sync_token is None)

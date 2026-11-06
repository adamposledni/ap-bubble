"""Ingest job: syncs the own Outlook calendars of every Microsoft account into L0.

Events come as a calendar view of a fixed window, so occurrences need no expansion. Graph v1.0
documents delta only for the default calendar's view; other calendars load fully on every run,
and the payload hashes keep those reruns cheap.
"""

import sqlite3
from functools import partial

import requests

from bubble_core.accounts import Account
from bubble_core.job_log import JobRun, job_run
from bubble_core.log import get_logger
from bubble_ingest.l0_sync import (
    ContainerChanges,
    apply_changes,
    save_containers,
    sync_accounts,
    sync_container,
)
from bubble_ingest.microsoft import auth as microsoft_auth
from bubble_ingest.microsoft.calendar import api
from bubble_ingest.microsoft.calendar.mapping import SOURCE, calendar_to_item, to_item
from bubble_ingest.microsoft.graph import Json

JOB_NAME = f"ingest.{SOURCE}"
SYNC_FROM = "2026-01-01T00:00:00Z"  # older history is not loaded yet, see other/TODO.md
# Fixed, because the delta link encodes the window: this year and next; see other/TODO.md.
SYNC_UNTIL = "2028-01-01T00:00:00Z"
WINDOW = api.Window(SYNC_FROM, SYNC_UNTIL)
_NO_CURSOR = ""  # fully loaded calendars keep no cursor; a later delta starts from scratch

logger = get_logger(__name__)


def sync_all(conn: sqlite3.Connection) -> None:
    sync_accounts(conn, "microsoft", sync_account)


def sync_account(conn: sqlite3.Connection, account: Account) -> None:
    with job_run(conn, JOB_NAME, account.key) as run:
        session = microsoft_auth.session_for(account.key)
        calendars = _own_calendars(api.list_calendars(session))
        save_containers(conn, account, SOURCE, [calendar_to_item(c) for c in calendars], run)
        for calendar in calendars:
            _sync_calendar(conn, account, session, calendar, run)


def _own_calendars(calendars: list[Json]) -> list[Json]:
    """Calendars owned like the default one; calendars shared by others are skipped."""
    default = next((c for c in calendars if c.get("isDefaultCalendar")), None)
    if default is None:
        raise ValueError("The mailbox has no default calendar")
    own = [c for c in calendars if _owner(c) == _owner(default)]
    logger.debug("%d of %d calendars are the account's own", len(own), len(calendars))
    return own


def _owner(calendar: Json) -> str:
    return (calendar.get("owner") or {}).get("address", "").lower()


def _sync_calendar(
    conn: sqlite3.Connection,
    account: Account,
    session: requests.Session,
    calendar: Json,
    run: JobRun,
) -> None:
    calendar_id = calendar["id"]
    if calendar.get("isDefaultCalendar"):
        fetch = partial(_fetch_changes, session, calendar_id)
        sync_container(conn, account, SOURCE, calendar_id, fetch, run)
    else:
        apply_changes(conn, account, SOURCE, calendar_id, _load_fully(session, calendar_id), run)


def _fetch_changes(
    session: requests.Session, calendar_id: str, delta_link: str | None
) -> ContainerChanges:
    changes = api.default_calendar_changes(session, WINDOW, delta_link)
    items = [to_item(calendar_id, event) for event in changes.events]
    return ContainerChanges(items, changes.delta_link, full_load=delta_link is None)


def _load_fully(session: requests.Session, calendar_id: str) -> ContainerChanges:
    events = api.calendar_view(session, calendar_id, WINDOW)
    items = [to_item(calendar_id, event) for event in events]
    return ContainerChanges(items, _NO_CURSOR, full_load=True)

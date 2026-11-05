"""Ingest job: syncs every task list of every Google account into L0.

The Tasks API has no sync tokens: the cursor is the RFC 3339 time the last fetch started, minus an
overlap, and the next fetch asks for tasks modified since then (updatedMin). Re-fetched unchanged
tasks are no-ops thanks to the payload hash in save_item.
"""

import sqlite3
from datetime import UTC, datetime, timedelta
from functools import partial

from google.auth.transport.requests import AuthorizedSession

from bubble_core.accounts import Account
from bubble_core.job_log import job_run
from bubble_core.log import get_logger
from bubble_ingest.google import auth as google_auth
from bubble_ingest.google.tasks import api
from bubble_ingest.google.tasks.mapping import SOURCE, tasklist_to_item, to_item
from bubble_ingest.l0_sync import (
    ContainerChanges,
    save_containers,
    sync_accounts,
    sync_container,
)

JOB_NAME = f"ingest.{SOURCE}"
# Covers clock skew between this PC and Google, and tasks written while a fetch runs.
CURSOR_OVERLAP = timedelta(minutes=1)

logger = get_logger(__name__)


def sync_all(conn: sqlite3.Connection) -> None:
    sync_accounts(conn, "google", sync_account)


def sync_account(conn: sqlite3.Connection, account: Account) -> None:
    with job_run(conn, JOB_NAME, account.key) as run:
        session = google_auth.session_for(account.key)
        tasklists = api.list_tasklists(session)
        save_containers(conn, account, SOURCE, [tasklist_to_item(t) for t in tasklists], run)
        for tasklist in tasklists:
            fetch = partial(_fetch_changes, session, tasklist["id"])
            sync_container(conn, account, SOURCE, tasklist["id"], fetch, run)


def _fetch_changes(
    session: AuthorizedSession, tasklist_id: str, updated_min: str | None
) -> ContainerChanges:
    next_cursor = _cursor_before(datetime.now(UTC))
    tasks = api.list_tasks(session, tasklist_id, updated_min)
    items = [to_item(tasklist_id, task) for task in tasks]
    logger.trace("Next cursor of task list %s: %s", tasklist_id, next_cursor)
    return ContainerChanges(items, next_cursor, full_load=updated_min is None)


def _cursor_before(moment: datetime) -> str:
    return (moment - CURSOR_OVERLAP).strftime("%Y-%m-%dT%H:%M:%SZ")

"""Ingest job: syncs every To Do list of every Microsoft account into L0.

Each list is tracked with tasks/delta: the cursor is the delta link, and an expired one falls back
to a full load. Everything is loaded, completed tasks and old ones included.
"""

import sqlite3
from functools import partial

import requests

from bubble_core.accounts import Account
from bubble_core.job_log import job_run
from bubble_core.log import get_logger
from bubble_ingest.l0_sync import ContainerChanges, save_containers, sync_accounts, sync_container
from bubble_ingest.microsoft import auth as microsoft_auth
from bubble_ingest.microsoft.todo import api
from bubble_ingest.microsoft.todo.mapping import SOURCE, tasklist_to_item, to_item

JOB_NAME = f"ingest.{SOURCE}"

logger = get_logger(__name__)


def sync_all(conn: sqlite3.Connection) -> None:
    sync_accounts(conn, "microsoft", sync_account)


def sync_account(conn: sqlite3.Connection, account: Account) -> None:
    with job_run(conn, JOB_NAME, account.key) as run:
        session = microsoft_auth.session_for(account.key)
        tasklists = api.list_tasklists(session)
        save_containers(conn, account, SOURCE, [tasklist_to_item(t) for t in tasklists], run)
        for tasklist in tasklists:
            fetch = partial(_fetch_changes, session, tasklist["id"])
            sync_container(conn, account, SOURCE, tasklist["id"], fetch, run)


def _fetch_changes(
    session: requests.Session, tasklist_id: str, delta_link: str | None
) -> ContainerChanges:
    changes = api.task_changes(session, tasklist_id, delta_link)
    items = [to_item(tasklist_id, task) for task in changes.tasks]
    logger.trace("Mapped %d tasks of To Do list %s", len(items), tasklist_id)
    return ContainerChanges(items, changes.delta_link, full_load=delta_link is None)

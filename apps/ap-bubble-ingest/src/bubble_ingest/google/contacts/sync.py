"""Ingest job: syncs the contacts and the other contacts of every Google account into L0."""

import sqlite3
from functools import partial

from google.auth.transport.requests import AuthorizedSession

from bubble_core.accounts import Account
from bubble_core.job_log import job_run
from bubble_core.log import get_logger
from bubble_ingest.google import auth as google_auth
from bubble_ingest.google.contacts import api
from bubble_ingest.google.contacts.mapping import SOURCE, to_item
from bubble_ingest.l0_sync import ContainerChanges, sync_accounts, sync_container

JOB_NAME = f"ingest.{SOURCE}"
# L0 container per People API list: saved contacts, and people only interacted with.
_CONTAINERS = {"connections": api.CONNECTIONS, "other": api.OTHER_CONTACTS}

logger = get_logger(__name__)


def sync_all(conn: sqlite3.Connection) -> None:
    sync_accounts(conn, "google", sync_account)


def sync_account(conn: sqlite3.Connection, account: Account) -> None:
    with job_run(conn, JOB_NAME, account.key) as run:
        session = google_auth.session_for(account.key)
        for container_id, people_list in _CONTAINERS.items():
            fetch = partial(_fetch_changes, session, container_id, people_list)
            sync_container(conn, account, SOURCE, container_id, fetch, run)


def _fetch_changes(
    session: AuthorizedSession,
    container_id: str,
    people_list: api.PeopleList,
    sync_token: str | None,
) -> ContainerChanges:
    result = api.list_people(session, people_list, sync_token)
    items = [to_item(container_id, person) for person in result.people]
    logger.trace("Mapped %d people of %s", len(items), container_id)
    return ContainerChanges(items, result.next_sync_token, full_load=sync_token is None)

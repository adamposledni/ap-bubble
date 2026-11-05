import sqlite3
from typing import Any

import pytest

from bubble_core.accounts import Account
from bubble_ingest.google import auth as google_auth
from bubble_ingest.google.contacts import api
from bubble_ingest.google.contacts.sync import sync_account
from bubble_ingest.l0_sync import CursorExpired


class FakePeopleApi:
    """Serves scripted people per list path and records (path, sync_token) requests."""

    def __init__(self) -> None:
        self.people: dict[str, list[dict[str, Any]]] = {}
        self.token_expired = False
        self.requests: list[tuple[str, str | None]] = []

    def list_people(
        self, session: object, people_list: api.PeopleList, sync_token: str | None
    ) -> api.PeopleChanges:
        self.requests.append((people_list.path, sync_token))
        if sync_token and self.token_expired:
            raise CursorExpired(people_list.path)
        people = list(self.people.get(people_list.path, []))
        return api.PeopleChanges(people, f"token-{len(self.requests)}")


@pytest.fixture
def fake_api(monkeypatch: pytest.MonkeyPatch) -> FakePeopleApi:
    fake = FakePeopleApi()
    monkeypatch.setattr(google_auth, "session_for", lambda account_key: object())
    monkeypatch.setattr(api, "list_people", fake.list_people)
    return fake


def _person(resource_name: str, deleted: bool = False) -> dict[str, Any]:
    return {"resourceName": resource_name, "metadata": {"deleted": deleted}}


def _rows(conn: sqlite3.Connection) -> dict[str, tuple[str, int]]:
    rows = conn.execute("SELECT container_id, external_id, deleted FROM l0_items").fetchall()
    return {row["external_id"]: (row["container_id"], row["deleted"]) for row in rows}


def test_first_sync_loads_both_lists_fully(
    conn: sqlite3.Connection, account: Account, fake_api: FakePeopleApi
) -> None:
    fake_api.people = {
        "people/me/connections": [_person("people/c1")],
        "otherContacts": [_person("otherContacts/c2")],
    }

    sync_account(conn, account)

    assert fake_api.requests == [("people/me/connections", None), ("otherContacts", None)]
    assert _rows(conn) == {"people/c1": ("connections", 0), "otherContacts/c2": ("other", 0)}


def test_next_sync_continues_from_stored_tokens(
    conn: sqlite3.Connection, account: Account, fake_api: FakePeopleApi
) -> None:
    sync_account(conn, account)
    sync_account(conn, account)

    assert fake_api.requests[2:] == [
        ("people/me/connections", "token-1"),
        ("otherContacts", "token-2"),
    ]


def test_incremental_deletion_flags_the_contact(
    conn: sqlite3.Connection, account: Account, fake_api: FakePeopleApi
) -> None:
    fake_api.people = {"people/me/connections": [_person("people/c1")]}
    sync_account(conn, account)
    fake_api.people = {"people/me/connections": [_person("people/c1", deleted=True)]}

    sync_account(conn, account)

    assert _rows(conn) == {"people/c1": ("connections", 1)}


def test_expired_token_falls_back_to_full_load_and_flags_missing_contacts(
    conn: sqlite3.Connection, account: Account, fake_api: FakePeopleApi
) -> None:
    fake_api.people = {"people/me/connections": [_person("people/c1"), _person("people/c2")]}
    sync_account(conn, account)
    fake_api.people = {"people/me/connections": [_person("people/c1")]}
    fake_api.token_expired = True

    sync_account(conn, account)

    assert fake_api.requests[2:4] == [
        ("people/me/connections", "token-1"),
        ("people/me/connections", None),
    ]
    assert _rows(conn) == {"people/c1": ("connections", 0), "people/c2": ("connections", 1)}


def test_sync_is_recorded_as_job_run(
    conn: sqlite3.Connection, account: Account, fake_api: FakePeopleApi
) -> None:
    fake_api.people = {
        "people/me/connections": [_person("people/c1")],
        "otherContacts": [_person("otherContacts/c2")],
    }

    sync_account(conn, account)

    row = conn.execute("SELECT * FROM lm_job_runs").fetchone()
    assert (row["job_name"], row["scope"], row["status"], row["items_processed"]) == (
        "ingest.google_contacts",
        "google:me@gmail.com",
        "succeeded",
        2,
    )

import sqlite3
from typing import Any

import pytest

from bubble_core.accounts import Account
from bubble_ingest.google import auth as google_auth
from bubble_ingest.google.calendar import api
from bubble_ingest.google.calendar.sync import sync_account
from bubble_ingest.l0_sync import CursorExpired


class FakeCalendarApi:
    """Serves scripted events for every calendar and records (calendar_id, sync_token) requests."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.token_expired = False
        self.requests: list[tuple[str, str | None]] = []

    def list_events(
        self, session: object, calendar_id: str, sync_token: str | None, time_min: str
    ) -> api.EventChanges:
        self.requests.append((calendar_id, sync_token))
        if sync_token and self.token_expired:
            raise CursorExpired(calendar_id)
        return api.EventChanges(list(self.events), f"token-{len(self.requests)}")


@pytest.fixture
def fake_api(monkeypatch: pytest.MonkeyPatch) -> FakeCalendarApi:
    fake = FakeCalendarApi()
    calendars = [
        {"id": "cal", "accessRole": "owner"},
        {"id": "busy", "accessRole": "freeBusyReader"},
    ]
    monkeypatch.setattr(google_auth, "session_for", lambda account_key: object())
    monkeypatch.setattr(api, "list_calendars", lambda session: calendars)
    monkeypatch.setattr(api, "list_events", fake.list_events)
    return fake


def _event(event_id: str) -> dict[str, Any]:
    return {"id": event_id, "status": "confirmed", "start": {"date": "2026-03-05"}}


def _deleted_flags(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute("SELECT external_id, deleted FROM l0_items").fetchall()
    return {row["external_id"]: row["deleted"] for row in rows}


def test_first_sync_loads_readable_calendars_fully(
    conn: sqlite3.Connection, account: Account, fake_api: FakeCalendarApi
) -> None:
    fake_api.events = [_event("e1")]

    sync_account(conn, account)

    assert fake_api.requests == [("cal", None)]
    assert _deleted_flags(conn) == {"e1": 0}


def test_next_sync_continues_from_stored_token(
    conn: sqlite3.Connection, account: Account, fake_api: FakeCalendarApi
) -> None:
    sync_account(conn, account)
    sync_account(conn, account)

    assert fake_api.requests == [("cal", None), ("cal", "token-1")]


def test_expired_token_falls_back_to_full_load_and_flags_missing_events(
    conn: sqlite3.Connection, account: Account, fake_api: FakeCalendarApi
) -> None:
    fake_api.events = [_event("e1"), _event("e2")]
    sync_account(conn, account)
    fake_api.events = [_event("e1")]
    fake_api.token_expired = True

    sync_account(conn, account)

    assert fake_api.requests[1:] == [("cal", "token-1"), ("cal", None)]
    assert _deleted_flags(conn) == {"e1": 0, "e2": 1}


def test_sync_is_recorded_as_job_run(
    conn: sqlite3.Connection, account: Account, fake_api: FakeCalendarApi
) -> None:
    fake_api.events = [_event("e1"), _event("e2")]

    sync_account(conn, account)

    row = conn.execute("SELECT * FROM lm_job_runs").fetchone()
    assert (row["job_name"], row["scope"], row["status"], row["items_processed"]) == (
        "ingest.google_calendar",
        "google:me@gmail.com",
        "succeeded",
        2,
    )

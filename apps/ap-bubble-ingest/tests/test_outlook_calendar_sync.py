import sqlite3
from typing import Any

import pytest

from bubble_core.accounts import Account, upsert_account
from bubble_ingest.l0_sync import CursorExpired
from bubble_ingest.microsoft import auth as microsoft_auth
from bubble_ingest.microsoft.calendar import api
from bubble_ingest.microsoft.calendar.sync import sync_account

ME = {"name": "Me", "address": "Me@Work.example"}
COLLEAGUE = {"name": "Colleague", "address": "colleague@work.example"}


class FakeCalendarApi:
    """Serves scripted events per calendar; records (calendar_id, delta_link) requests."""

    def __init__(self) -> None:
        self.calendars = [
            {"id": "cal", "name": "Calendar", "isDefaultCalendar": True, "owner": ME},
            {"id": "other", "name": "Holidays", "isDefaultCalendar": False, "owner": ME},
            {"id": "shared", "name": "Colleague", "isDefaultCalendar": False, "owner": COLLEAGUE},
        ]
        self.events: dict[str, list[dict[str, Any]]] = {"cal": [], "other": []}
        self.link_expired = False
        self.requests: list[tuple[str, str | None]] = []

    def default_calendar_changes(
        self, session: object, window: api.Window, delta_link: str | None
    ) -> api.EventChanges:
        self.requests.append(("cal", delta_link))
        if delta_link and self.link_expired:
            raise CursorExpired("cal")
        return api.EventChanges(list(self.events["cal"]), f"delta-{len(self.requests)}")

    def calendar_view(
        self, session: object, calendar_id: str, window: api.Window
    ) -> list[dict[str, Any]]:
        self.requests.append((calendar_id, None))
        return list(self.events[calendar_id])


@pytest.fixture
def fake_api(monkeypatch: pytest.MonkeyPatch) -> FakeCalendarApi:
    fake = FakeCalendarApi()
    monkeypatch.setattr(microsoft_auth, "session_for", lambda account_key: object())
    monkeypatch.setattr(api, "list_calendars", lambda session: fake.calendars)
    monkeypatch.setattr(api, "default_calendar_changes", fake.default_calendar_changes)
    monkeypatch.setattr(api, "calendar_view", fake.calendar_view)
    return fake


@pytest.fixture
def work(conn: sqlite3.Connection) -> Account:
    return upsert_account(conn, "microsoft", "me@work.example", "work")


def _event(event_id: str) -> dict[str, Any]:
    when = {"dateTime": "2026-03-05T09:00:00.0000000", "timeZone": "UTC"}
    return {"id": event_id, "type": "singleInstance", "isAllDay": False, "start": when, "end": when}


def _flags(conn: sqlite3.Connection, kind: str = "event") -> dict[str, int]:
    rows = conn.execute("SELECT external_id, deleted FROM l0_items WHERE kind = ?", (kind,))
    return {row["external_id"]: row["deleted"] for row in rows}


def test_first_sync_loads_own_calendars_fully_and_skips_shared_ones(
    conn: sqlite3.Connection, work: Account, fake_api: FakeCalendarApi
) -> None:
    fake_api.events = {"cal": [_event("e1")], "other": [_event("h1")]}

    sync_account(conn, work)

    assert fake_api.requests == [("cal", None), ("other", None)]
    assert _flags(conn) == {"e1": 0, "h1": 0}
    assert _flags(conn, "calendar") == {"cal": 0, "other": 0}


def test_next_sync_continues_the_default_calendar_from_its_delta_link(
    conn: sqlite3.Connection, work: Account, fake_api: FakeCalendarApi
) -> None:
    sync_account(conn, work)
    sync_account(conn, work)

    assert fake_api.requests[2:] == [("cal", "delta-1"), ("other", None)]


def test_removed_entries_of_a_delta_flag_their_events(
    conn: sqlite3.Connection, work: Account, fake_api: FakeCalendarApi
) -> None:
    fake_api.events["cal"] = [_event("e1"), _event("e2")]
    sync_account(conn, work)
    fake_api.events["cal"] = [{"id": "e1", "@removed": {"reason": "deleted"}}]

    sync_account(conn, work)

    assert _flags(conn) == {"e1": 1, "e2": 0}


def test_expired_delta_link_falls_back_to_a_full_load(
    conn: sqlite3.Connection, work: Account, fake_api: FakeCalendarApi
) -> None:
    fake_api.events["cal"] = [_event("e1"), _event("e2")]
    sync_account(conn, work)
    fake_api.events["cal"] = [_event("e1")]
    fake_api.link_expired = True

    sync_account(conn, work)

    assert fake_api.requests[2:4] == [("cal", "delta-1"), ("cal", None)]
    assert _flags(conn) == {"e1": 0, "e2": 1}


def test_fully_loaded_calendar_flags_events_it_no_longer_returns(
    conn: sqlite3.Connection, work: Account, fake_api: FakeCalendarApi
) -> None:
    fake_api.events["other"] = [_event("h1"), _event("h2")]
    sync_account(conn, work)
    fake_api.events["other"] = [_event("h2")]

    sync_account(conn, work)

    assert _flags(conn) == {"h1": 1, "h2": 0}


def test_removed_calendar_is_flagged(
    conn: sqlite3.Connection, work: Account, fake_api: FakeCalendarApi
) -> None:
    sync_account(conn, work)
    fake_api.calendars = fake_api.calendars[:1]

    sync_account(conn, work)

    assert _flags(conn, "calendar") == {"cal": 0, "other": 1}


def test_sync_is_recorded_as_job_run(
    conn: sqlite3.Connection, work: Account, fake_api: FakeCalendarApi
) -> None:
    fake_api.events = {"cal": [_event("e1")], "other": [_event("h1"), _event("h2")]}

    sync_account(conn, work)

    row = conn.execute("SELECT * FROM lm_job_runs").fetchone()
    assert (row["job_name"], row["scope"], row["status"], row["items_processed"]) == (
        "ingest.outlook_calendar",
        "microsoft:me@work.example",
        "succeeded",
        3,
    )

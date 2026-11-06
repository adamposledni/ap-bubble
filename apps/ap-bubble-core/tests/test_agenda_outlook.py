import sqlite3
from collections.abc import Callable
from datetime import date
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from bubble_core.accounts import Account
from bubble_core.items import Item, save_item
from bubble_core.queries.agenda import agenda

PRAGUE = ZoneInfo("Europe/Prague")
WEEK_OF_9_MARCH = (date(2026, 3, 9), 7)  # 2026-03-08T23:00Z to 2026-03-15T23:00Z
SOURCE = "outlook_calendar"

type SaveEvent = Callable[..., None]


@pytest.fixture
def save(conn: sqlite3.Connection, account: Account, run_id: int) -> Callable[..., None]:
    """Saves an Outlook item as the ingest job would: (kind, container, id, times, payload)."""

    def save(
        kind: str,
        container_id: str,
        external_id: str,
        start: str | None,
        end: str | None,
        payload: dict[str, Any],
        deleted: bool = False,
    ) -> None:
        item = Item(
            source=SOURCE,
            container_id=container_id,
            external_id=external_id,
            kind=kind,
            title=payload.get("subject") or payload.get("name"),
            starts_at=start,
            ends_at=end,
            deleted=deleted,
            payload={"id": external_id, **payload},
        )
        save_item(conn, account.id, item, run_id)
        conn.commit()

    return save


@pytest.fixture
def save_event(save: Callable[..., None]) -> SaveEvent:
    save("calendar", "", "work", None, None, {"name": "Work"})

    def save_event(
        event_id: str, start: str, end: str, deleted: bool = False, **payload: Any
    ) -> None:
        payload = {"type": "singleInstance", "isAllDay": "T" not in start} | payload
        save("event", "work", event_id, start, end, payload, deleted)

    return save_event


def _utc(day_and_time: str) -> str:
    return f"2026-03-{day_and_time}:00+00:00"


def _week(conn: sqlite3.Connection) -> list[tuple[str | None, str]]:
    return [(e.title, e.start) for e in agenda(conn, *WEEK_OF_9_MARCH, PRAGUE)]


def test_events_are_listed_with_their_calendar_and_location(
    conn: sqlite3.Connection, save_event: SaveEvent
) -> None:
    location = {"displayName": "Room 1"}
    save_event("in", _utc("10T09:00"), _utc("10T10:00"), subject="Review", location=location)
    save_event("out", _utc("20T09:00"), _utc("20T10:00"), subject="Later")

    [event] = agenda(conn, *WEEK_OF_9_MARCH, PRAGUE)

    assert (event.title, event.calendar, event.location) == ("Review", "Work", "Room 1")
    assert (event.start, event.end, event.all_day, event.recurring) == (
        "2026-03-10T09:00:00+00:00",
        "2026-03-10T10:00:00+00:00",
        False,
        False,
    )


def test_all_day_events_keep_their_dates(conn: sqlite3.Connection, save_event: SaveEvent) -> None:
    save_event("d", "2026-03-11", "2026-03-13", subject="Offsite", location={"displayName": ""})

    [event] = agenda(conn, *WEEK_OF_9_MARCH, PRAGUE)

    assert (event.start, event.end, event.all_day, event.location) == (
        "2026-03-11",
        "2026-03-13",
        True,
        None,
    )


def test_window_edges_follow_the_local_days(
    conn: sqlite3.Connection, save_event: SaveEvent
) -> None:
    save_event("late", _utc("15T22:30"), _utc("15T22:45"), subject="Last local hour")
    save_event("next", _utc("15T23:00"), _utc("15T23:30"), subject="Next week")
    save_event("before", "2026-03-08", "2026-03-09", subject="Day before")
    save_event("after", "2026-03-16", "2026-03-17", subject="Day after")

    assert _week(conn) == [("Last local hour", "2026-03-15T22:30:00+00:00")]


def test_occurrences_and_exceptions_are_recurring_and_series_masters_left_out(
    conn: sqlite3.Connection, save_event: SaveEvent
) -> None:
    save_event("m", _utc("09T08:00"), _utc("09T08:15"), subject="Standup", type="seriesMaster")
    save_event("o", _utc("09T08:00"), _utc("09T08:15"), subject="Standup", type="occurrence")
    save_event("x", _utc("10T09:00"), _utc("10T09:15"), subject="Moved", type="exception")

    events = agenda(conn, *WEEK_OF_9_MARCH, PRAGUE)

    assert [(e.title, e.recurring) for e in events] == [("Standup", True), ("Moved", True)]


def test_cancelled_events_and_removed_calendars_are_hidden(
    conn: sqlite3.Connection, save_event: SaveEvent
) -> None:
    save_event("c", _utc("10T09:00"), _utc("10T10:00"), deleted=True, subject="Cancelled")
    save_event("e", _utc("11T09:00"), _utc("11T10:00"), subject="Kept")
    assert _week(conn) == [("Kept", "2026-03-11T09:00:00+00:00")]

    conn.execute("UPDATE l0_items SET deleted = 1 WHERE kind = 'calendar'")

    assert agenda(conn, *WEEK_OF_9_MARCH, PRAGUE) == []


def test_outlook_and_google_events_are_merged_in_order(
    conn: sqlite3.Connection, save_event: SaveEvent, store_item: Callable[..., None]
) -> None:
    store_item("google_calendar", "calendar", "", "cal", {"summary": "Mine"})
    dentist = {
        "summary": "Dentist",
        "start": {"dateTime": "2026-03-10T10:00:00+01:00"},
        "end": {"dateTime": "2026-03-10T11:00:00+01:00"},
    }
    store_item("google_calendar", "event", "cal", "g", dentist)
    save_event("early", _utc("10T08:00"), _utc("10T08:30"), subject="Standup")
    save_event("late", _utc("10T12:00"), _utc("10T13:00"), subject="Lunch")

    assert [(e.title, e.calendar) for e in agenda(conn, *WEEK_OF_9_MARCH, PRAGUE)] == [
        ("Standup", "Work"),
        ("Dentist", "Mine"),
        ("Lunch", "Work"),
    ]

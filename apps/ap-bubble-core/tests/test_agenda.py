import sqlite3
from collections.abc import Callable
from datetime import date
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from bubble_core.queries.agenda import agenda

PRAGUE = ZoneInfo("Europe/Prague")
WEEK_OF_9_MARCH = (date(2026, 3, 9), 7)

type SaveEvent = Callable[..., None]


@pytest.fixture
def save_event(store_item: Callable[..., None]) -> SaveEvent:
    store_item("google_calendar", "calendar", "", "cal", {"summary": "Mine"})

    def save_event(event_id: str, deleted: bool = False, **payload: Any) -> None:
        store_item("google_calendar", "event", "cal", event_id, payload, deleted)

    return save_event


def _at(local: str) -> dict[str, str]:
    """A timed start/end in Prague, in winter time (UTC+1)."""
    return {"dateTime": f"{local}+01:00", "timeZone": "Europe/Prague"}


def _week(conn: sqlite3.Connection) -> list[tuple[str | None, str]]:
    return [(e.title, e.start) for e in agenda(conn, *WEEK_OF_9_MARCH, PRAGUE)]


def test_events_in_the_window_are_listed_in_utc(
    conn: sqlite3.Connection, save_event: SaveEvent
) -> None:
    save_event("in", summary="Dentist", start=_at("2026-03-10T10:00"), end=_at("2026-03-10T11:00"))
    save_event("out", summary="Later", start=_at("2026-03-20T10:00"), end=_at("2026-03-20T11:00"))

    [event] = agenda(conn, *WEEK_OF_9_MARCH, PRAGUE)

    assert (event.title, event.calendar, event.all_day) == ("Dentist", "Mine", False)
    assert (event.start, event.end) == ("2026-03-10T09:00:00+00:00", "2026-03-10T10:00:00+00:00")


def test_all_day_events_keep_their_dates(conn: sqlite3.Connection, save_event: SaveEvent) -> None:
    save_event("d", summary="Name day", start={"date": "2026-03-11"}, end={"date": "2026-03-12"})

    [event] = agenda(conn, *WEEK_OF_9_MARCH, PRAGUE)

    assert (event.start, event.end, event.all_day) == ("2026-03-11", "2026-03-12", True)


def test_series_is_expanded_without_excluded_dates(
    conn: sqlite3.Connection, save_event: SaveEvent
) -> None:
    rules = ["RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE", "EXDATE;TZID=Europe/Prague:20260310T090000"]
    save_event("s", summary="Standup", start=_at("2026-03-02T09:00"), end=_at("2026-03-02T09:15"),
               recurrence=rules)  # fmt: skip

    assert _week(conn) == [
        ("Standup", "2026-03-09T08:00:00+00:00"),
        ("Standup", "2026-03-11T08:00:00+00:00"),
    ]


def test_exceptions_replace_their_occurrences(
    conn: sqlite3.Connection, save_event: SaveEvent
) -> None:
    weekly = ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE"]
    save_event("s", summary="Sync", start=_at("2026-03-02T09:00"), end=_at("2026-03-02T10:00"),
               recurrence=weekly)  # fmt: skip
    moved = {"recurringEventId": "s", "originalStartTime": _at("2026-03-09T09:00")}
    save_event("s_1", summary="Sync moved", start=_at("2026-03-09T14:00"),
               end=_at("2026-03-09T15:00"), **moved)  # fmt: skip
    cancelled = {"recurringEventId": "s", "originalStartTime": _at("2026-03-11T09:00")}
    save_event("s_2", deleted=True, status="cancelled", **cancelled)

    assert _week(conn) == [("Sync moved", "2026-03-09T13:00:00+00:00")]


def test_events_of_removed_calendars_are_hidden(
    conn: sqlite3.Connection, save_event: SaveEvent
) -> None:
    save_event("e", summary="Gone", start={"date": "2026-03-10"}, end={"date": "2026-03-11"})
    conn.execute("UPDATE l0_items SET deleted = 1 WHERE kind = 'calendar'")

    assert agenda(conn, *WEEK_OF_9_MARCH, PRAGUE) == []

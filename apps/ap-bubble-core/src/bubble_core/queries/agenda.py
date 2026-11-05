"""Agenda: events of all live calendars in a range of days, recurring series as occurrences.

L0 keeps a recurring event as its series plus exceptions (moved or cancelled occurrences, which
point at the series with recurringEventId and originalStartTime). The series is expanded here;
an exception replaces the occurrence it was made from.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from bubble_core.log import get_logger
from bubble_core.queries.event_times import Span, as_text, day_window, moment_of, span_of
from bubble_core.queries.recurrence import occurrence_starts

_SOURCE = "google_calendar"

type CalendarKey = tuple[int, str]  # (account id, calendar id)
type SeriesKey = tuple[int, str, str]  # (account id, calendar id, series event id)

logger = get_logger(__name__)


@dataclass(frozen=True)
class AgendaEvent:
    key: str  # unique per occurrence
    calendar: str | None
    title: str | None
    start: str  # vault UTC timestamp, or YYYY-MM-DD for all-day events
    end: str  # exclusive
    all_day: bool
    location: str | None
    recurring: bool


@dataclass(frozen=True)
class _Event:
    id: int
    calendar_key: CalendarKey
    deleted: bool
    payload: dict[str, Any]


def agenda(conn: sqlite3.Connection, first_day: date, days: int, tz: ZoneInfo) -> list[AgendaEvent]:
    window = day_window(first_day, days, tz)
    calendars = _live_calendars(conn)
    events = [e for e in _events(conn) if e.calendar_key in calendars]
    replaced = _replaced_starts(events, tz)
    found: list[tuple[Span, AgendaEvent]] = []
    for event in (e for e in events if not e.deleted):
        try:
            found += _occurrences(event, calendars[event.calendar_key], replaced, window, tz)
        except (ValueError, KeyError):
            logger.warning("Skipped event %d: its time or recurrence is not understood", event.id)
    found.sort(key=lambda pair: (pair[0].start, not pair[0].all_day, pair[1].title or ""))
    logger.debug("Agenda from %s for %d days: %d events", first_day, days, len(found))
    return [agenda_event for _, agenda_event in found]


def _occurrences(
    event: _Event,
    calendar: str | None,
    replaced: dict[SeriesKey, set[datetime]],
    window: tuple[datetime, datetime],
    tz: ZoneInfo,
) -> list[tuple[Span, AgendaEvent]]:
    span = span_of(event.payload, tz)
    recurrence = event.payload.get("recurrence")
    if not recurrence:
        recurring = "recurringEventId" in event.payload
        spans = [span] if span.overlaps(*window) else []
        return [(s, _to_agenda(event, calendar, s, str(event.id), recurring)) for s in spans]
    skip = replaced.get((*event.calendar_key, event.payload["id"]), set())
    after, before = window[0] - (span.end - span.start), window[1]
    starts = occurrence_starts(span.start, recurrence, after, before)
    spans = [span.moved_to(start) for start in starts if start not in skip]
    spans = [s for s in spans if s.overlaps(*window)]
    return [(s, _to_agenda(event, calendar, s, f"{event.id}@{s.start}", True)) for s in spans]


def _to_agenda(
    event: _Event, calendar: str | None, span: Span, key: str, recurring: bool
) -> AgendaEvent:
    return AgendaEvent(
        key=key,
        calendar=calendar,
        title=event.payload.get("summary"),
        start=as_text(span.start, span.all_day),
        end=as_text(span.end, span.all_day),
        all_day=span.all_day,
        location=event.payload.get("location"),
        recurring=recurring,
    )


def _replaced_starts(events: list[_Event], tz: ZoneInfo) -> dict[SeriesKey, set[datetime]]:
    """Original starts of the occurrences that exceptions moved or cancelled, per series."""
    replaced: dict[SeriesKey, set[datetime]] = {}
    for event in events:
        series_id = event.payload.get("recurringEventId")
        original = event.payload.get("originalStartTime")
        if series_id and original:
            key = (*event.calendar_key, series_id)
            replaced.setdefault(key, set()).add(moment_of(original, tz))
    return replaced


def _live_calendars(conn: sqlite3.Connection) -> dict[CalendarKey, str | None]:
    rows = conn.execute(
        "SELECT account_id, external_id, title FROM l0_items "
        "WHERE source = ? AND kind = 'calendar' AND deleted = 0",
        (_SOURCE,),
    ).fetchall()
    return {(row["account_id"], row["external_id"]): row["title"] for row in rows}


def _events(conn: sqlite3.Connection) -> list[_Event]:
    """Live events, plus deleted exceptions: a cancelled occurrence still removes its slot."""
    rows = conn.execute(
        "SELECT id, account_id, container_id, deleted, payload FROM l0_items "
        "WHERE source = ? AND kind = 'event' "
        "AND (deleted = 0 OR json_extract(payload, '$.recurringEventId') IS NOT NULL)",
        (_SOURCE,),
    ).fetchall()
    return [
        _Event(
            id=row["id"],
            calendar_key=(row["account_id"], row["container_id"]),
            deleted=bool(row["deleted"]),
            payload=json.loads(row["payload"]),
        )
        for row in rows
    ]

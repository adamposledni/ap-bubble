"""Google Calendar events for the agenda, recurring series expanded into occurrences.

L0 keeps a recurring event as its series plus exceptions (moved or cancelled occurrences, which
point at the series with recurringEventId and originalStartTime). The series is expanded here;
an exception replaces the occurrence it was made from.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from bubble_core.log import get_logger
from bubble_core.queries.agenda_event import (
    AgendaEvent,
    Calendar,
    CalendarKey,
    Found,
    Window,
    live_calendars,
)
from bubble_core.queries.event_times import Span, as_text, moment_of, span_of
from bubble_core.queries.recurrence import occurrence_starts

_SOURCE = "google_calendar"

type SeriesKey = tuple[int, str, str]  # (account id, calendar id, series event id)

logger = get_logger(__name__)


@dataclass(frozen=True)
class _Event:
    id: int
    calendar_key: CalendarKey
    deleted: bool
    payload: dict[str, Any]


def google_events(conn: sqlite3.Connection, window: Window, tz: ZoneInfo) -> list[Found]:
    calendars = live_calendars(conn, _SOURCE)
    events = [e for e in _events(conn) if e.calendar_key in calendars]
    replaced = _replaced_starts(events, tz)
    found: list[Found] = []
    for event in (e for e in events if not e.deleted):
        try:
            found += _occurrences(event, calendars[event.calendar_key], replaced, window, tz)
        except (ValueError, KeyError):
            logger.warning("Skipped event %d: its time or recurrence is not understood", event.id)
    logger.trace("%d Google events in the window", len(found))
    return found


def _occurrences(
    event: _Event,
    calendar: Calendar,
    replaced: dict[SeriesKey, set[datetime]],
    window: Window,
    tz: ZoneInfo,
) -> list[Found]:
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
    event: _Event, calendar: Calendar, span: Span, key: str, recurring: bool
) -> AgendaEvent:
    return AgendaEvent(
        key=key,
        calendar=calendar.name,
        context=calendar.context,
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

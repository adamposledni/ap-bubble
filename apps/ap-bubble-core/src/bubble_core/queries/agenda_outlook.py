"""Outlook events for the agenda: L0 holds a calendar view, so each row is one occurrence.

Series masters (calendarView delta returns them too) are left out; their occurrences and
exceptions are rows of their own.
"""

import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bubble_core.log import get_logger
from bubble_core.queries.agenda_event import AgendaEvent, Calendar, Found, Window, live_calendars
from bubble_core.queries.event_times import Span, day_start

_SOURCE = "outlook_calendar"
_RECURRING_TYPES = {"occurrence", "exception"}
# Stored times mix UTC timestamps and plain dates: a day either side of the window keeps every
# candidate whatever the offset; the exact check follows on aware datetimes.
_MARGIN = timedelta(days=1)

logger = get_logger(__name__)


def outlook_events(conn: sqlite3.Connection, window: Window, tz: ZoneInfo) -> list[Found]:
    calendars = live_calendars(conn, _SOURCE)
    found: list[Found] = []
    for row in _candidates(conn, window):
        calendar_key = (row["account_id"], row["container_id"])
        if calendar_key in calendars:
            found += _found(row, calendars[calendar_key], window, tz)
    logger.trace("%d Outlook events in the window", len(found))
    return found


def _found(row: sqlite3.Row, calendar: Calendar, window: Window, tz: ZoneInfo) -> list[Found]:
    try:
        span = _span(row, tz)
    except ValueError:
        logger.warning("Skipped event %d: its time is not understood", row["id"])
        return []
    return [(span, _to_agenda(row, calendar))] if span.overlaps(*window) else []


def _span(row: sqlite3.Row, tz: ZoneInfo) -> Span:
    if row["all_day"]:
        return Span(day_start(row["starts_at"], tz), day_start(row["ends_at"], tz), all_day=True)
    start, end = datetime.fromisoformat(row["starts_at"]), datetime.fromisoformat(row["ends_at"])
    return Span(start, end, all_day=False)


def _to_agenda(row: sqlite3.Row, calendar: Calendar) -> AgendaEvent:
    return AgendaEvent(
        key=str(row["id"]),
        calendar=calendar.name,
        context=calendar.context,
        title=row["title"],
        start=row["starts_at"],
        end=row["ends_at"],
        all_day=bool(row["all_day"]),
        location=row["location"] or None,
        recurring=row["type"] in _RECURRING_TYPES,
    )


def _candidates(conn: sqlite3.Connection, window: Window) -> list[sqlite3.Row]:
    """Live single events, occurrences and exceptions stored within a day of the window."""
    return conn.execute(
        "SELECT id, account_id, container_id, title, starts_at, ends_at, "
        "json_extract(payload, '$.isAllDay') AS all_day, "
        "json_extract(payload, '$.type') AS type, "
        "json_extract(payload, '$.location.displayName') AS location "
        "FROM l0_items WHERE source = :source AND kind = 'event' AND deleted = 0 "
        "AND json_extract(payload, '$.type') IS NOT 'seriesMaster' "
        "AND starts_at < :before AND ends_at > :after",
        {
            "source": _SOURCE,
            "before": (window[1].date() + _MARGIN).isoformat(),
            "after": (window[0].date() - _MARGIN).isoformat(),
        },
    ).fetchall()

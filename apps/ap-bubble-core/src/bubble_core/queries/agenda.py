"""Agenda: events of all live calendars (Google and Outlook) in a range of days, as occurrences."""

import sqlite3
from datetime import date
from zoneinfo import ZoneInfo

from bubble_core.log import get_logger
from bubble_core.queries.agenda_event import AgendaEvent
from bubble_core.queries.agenda_google import google_events
from bubble_core.queries.agenda_outlook import outlook_events
from bubble_core.queries.event_times import day_window

logger = get_logger(__name__)


def agenda(conn: sqlite3.Connection, first_day: date, days: int, tz: ZoneInfo) -> list[AgendaEvent]:
    window = day_window(first_day, days, tz)
    found = google_events(conn, window, tz) + outlook_events(conn, window, tz)
    found.sort(key=lambda pair: (pair[0].start, not pair[0].all_day, pair[1].title or ""))
    logger.debug("Agenda from %s for %d days: %d events", first_day, days, len(found))
    return [agenda_event for _, agenda_event in found]

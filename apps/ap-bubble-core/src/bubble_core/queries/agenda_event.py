"""What the agenda lists, and what its calendar sources (Google, Outlook) share."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime

from bubble_core.queries.event_times import Span

type CalendarKey = tuple[int, str]  # (account id, calendar id)
type Window = tuple[datetime, datetime]
type Found = tuple[Span, AgendaEvent]  # the span filters and sorts, the event is listed


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


def live_calendars(conn: sqlite3.Connection, source: str) -> dict[CalendarKey, str | None]:
    """Names of a source's calendars that are not removed, by (account id, calendar id)."""
    rows = conn.execute(
        "SELECT account_id, external_id, title FROM l0_items "
        "WHERE source = ? AND kind = 'calendar' AND deleted = 0",
        (source,),
    ).fetchall()
    return {(row["account_id"], row["external_id"]): row["title"] for row in rows}

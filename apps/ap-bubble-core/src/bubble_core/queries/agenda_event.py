"""What the agenda lists, and what its calendar sources (Google, Outlook) share."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from bubble_core.accounts import Context
from bubble_core.queries.event_times import Span

type CalendarKey = tuple[int, str]  # (account id, calendar id)
type Window = tuple[datetime, datetime]
type Found = tuple[Span, AgendaEvent]  # the span filters and sorts, the event is listed


@dataclass(frozen=True)
class AgendaEvent:
    key: str  # unique per occurrence
    calendar: str | None
    context: Context  # of the calendar's account: work or personal
    title: str | None
    start: str  # vault UTC timestamp, or YYYY-MM-DD for all-day events
    end: str  # exclusive
    all_day: bool
    location: str | None
    recurring: bool


@dataclass(frozen=True)
class Calendar:
    name: str | None
    context: Context


def live_calendars(conn: sqlite3.Connection, source: str) -> dict[CalendarKey, Calendar]:
    """A source's calendars that are not removed, by (account id, calendar id)."""
    rows = conn.execute(
        "SELECT i.account_id, i.external_id, i.title, a.context FROM l0_items i "
        "JOIN lm_accounts a ON a.id = i.account_id "
        "WHERE i.source = ? AND i.kind = 'calendar' AND i.deleted = 0",
        (source,),
    ).fetchall()
    return {
        (row["account_id"], row["external_id"]): Calendar(
            row["title"], cast(Context, row["context"])
        )
        for row in rows
    }

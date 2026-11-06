"""Outlook calendars and their calendar views (occurrences, not series) from Graph v1.0."""

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests

from bubble_core.log import get_logger
from bubble_ingest.microsoft.graph import GRAPH_URL, Json, get_all_pages, get_delta

# Times in UTC and ids that survive moves; several preferences share one Prefer header.
HEADERS = {"Prefer": 'outlook.timezone="UTC", IdType="ImmutableId"'}
_PAGE_SIZE = 1000  # calendarView $top maximum

logger = get_logger(__name__)


@dataclass(frozen=True)
class Window:
    """Time range of a calendar view, ISO 8601 with offset."""

    start: str
    end: str

    def params(self) -> dict[str, Any]:
        return {"startDateTime": self.start, "endDateTime": self.end}


def list_calendars(session: requests.Session) -> list[Json]:
    calendars = get_all_pages(session, f"{GRAPH_URL}/me/calendars", None, HEADERS).items
    logger.debug("Fetched %d calendars", len(calendars))
    return calendars


@dataclass(frozen=True)
class EventChanges:
    events: list[Json]
    delta_link: str


def default_calendar_changes(
    session: requests.Session, window: Window, delta_link: str | None
) -> EventChanges:
    """Changes in the default calendar's view since delta_link, or all of it when there is none.

    v1.0 documents calendarView delta only for the default calendar (/me/calendarView).
    Removed events, and events changed outside the window, come as @removed entries.
    Raises CursorExpired when Graph no longer accepts the delta link.
    """
    url = f"{GRAPH_URL}/me/calendarView/delta"
    pages = get_delta(session, url, window.params(), delta_link, HEADERS)
    if not pages.delta_link:
        raise RuntimeError("Graph ended the calendar view delta without a delta link")
    logger.debug("Fetched %d changed events of the default calendar", len(pages.items))
    return EventChanges(pages.items, pages.delta_link)


def calendar_view(session: requests.Session, calendar_id: str, window: Window) -> list[Json]:
    """All single events, occurrences and exceptions of a calendar within the window."""
    url = f"{GRAPH_URL}/me/calendars/{quote(calendar_id, safe='')}/calendarView"
    params = window.params() | {"$top": _PAGE_SIZE}
    events = get_all_pages(session, url, params, HEADERS).items
    logger.debug("Fetched %d events of calendar %s", len(events), calendar_id)
    return events

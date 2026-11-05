"""Google Calendar API v3 over plain HTTP: the calendar list and event changes."""

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests
from google.auth.transport.requests import AuthorizedSession

from bubble_core.log import get_logger
from bubble_ingest.google.http import Json, get_all_pages
from bubble_ingest.l0_sync import CursorExpired

BASE_URL = "https://www.googleapis.com/calendar/v3"
_PAGE_SIZE = 2500  # API maximum
_HTTP_GONE = 410  # sync token no longer valid

logger = get_logger(__name__)


@dataclass(frozen=True)
class EventChanges:
    events: list[Json]
    next_sync_token: str


def list_calendars(session: AuthorizedSession) -> list[Json]:
    calendars, _ = get_all_pages(session, f"{BASE_URL}/users/me/calendarList", {})
    logger.debug("Fetched %d calendars", len(calendars))
    return calendars


def list_events(
    session: AuthorizedSession, calendar_id: str, sync_token: str | None, time_min: str
) -> EventChanges:
    """Events changed since sync_token, or all events from time_min on when there is no token.

    Recurring events come as the series plus its exceptions (not expanded); cancelled included.
    Raises CursorExpired when Google no longer accepts the sync token.
    """
    params: dict[str, Any] = {"maxResults": _PAGE_SIZE, "showDeleted": "true"}
    if sync_token:
        params["syncToken"] = sync_token
    else:
        params["timeMin"] = time_min
    url = f"{BASE_URL}/calendars/{quote(calendar_id, safe='')}/events"
    try:
        events, last_page = get_all_pages(session, url, params)
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == _HTTP_GONE:
            raise CursorExpired(calendar_id) from error
        raise
    return EventChanges(events, last_page["nextSyncToken"])

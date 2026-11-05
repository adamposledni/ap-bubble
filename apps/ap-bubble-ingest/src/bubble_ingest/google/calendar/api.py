"""Google Calendar API v3 over plain HTTP: the calendar list and event changes."""

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from google.auth.transport.requests import AuthorizedSession

from bubble_core.log import get_logger

BASE_URL = "https://www.googleapis.com/calendar/v3"
_PAGE_SIZE = 2500  # API maximum
_HTTP_TIMEOUT_SECONDS = 30
_HTTP_GONE = 410

type Json = dict[str, Any]

logger = get_logger(__name__)


class SyncTokenExpired(Exception):
    """The sync token is no longer valid; the calendar needs a full load."""


@dataclass(frozen=True)
class EventChanges:
    events: list[Json]
    next_sync_token: str


def list_calendars(session: AuthorizedSession) -> list[Json]:
    calendars, _ = _get_all_pages(session, f"{BASE_URL}/users/me/calendarList", {})
    logger.debug("Fetched %d calendars", len(calendars))
    return calendars


def list_events(
    session: AuthorizedSession, calendar_id: str, sync_token: str | None, time_min: str
) -> EventChanges:
    """Events changed since sync_token, or all events from time_min on when there is no token.

    Recurring events come as the series plus its exceptions (not expanded); cancelled included.
    """
    params: dict[str, Any] = {"maxResults": _PAGE_SIZE, "showDeleted": "true"}
    if sync_token:
        params["syncToken"] = sync_token
    else:
        params["timeMin"] = time_min
    url = f"{BASE_URL}/calendars/{quote(calendar_id, safe='')}/events"
    events, last_page = _get_all_pages(session, url, params)
    return EventChanges(events, last_page["nextSyncToken"])


def _get_all_pages(
    session: AuthorizedSession, url: str, params: dict[str, Any]
) -> tuple[list[Json], Json]:
    """Follow nextPageToken; return all items and the last page (it holds nextSyncToken)."""
    items: list[Json] = []
    params = dict(params)
    while True:
        page = _get(session, url, params)
        items.extend(page.get("items", []))
        if "nextPageToken" not in page:
            return items, page
        params["pageToken"] = page["nextPageToken"]


def _get(session: AuthorizedSession, url: str, params: dict[str, Any]) -> Json:
    response = session.get(url, params=params, timeout=_HTTP_TIMEOUT_SECONDS)
    logger.trace("GET %s -> %d", url, response.status_code)
    if response.status_code == _HTTP_GONE:
        raise SyncTokenExpired(url)
    response.raise_for_status()
    return response.json()

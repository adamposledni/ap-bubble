"""Microsoft Graph over plain HTTP: paging (@odata.nextLink), delta links, throttling retries."""

import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import requests

from bubble_core.log import get_logger
from bubble_ingest.l0_sync import CursorExpired

GRAPH_URL = "https://graph.microsoft.com/v1.0"
HTTP_TIMEOUT_SECONDS = 60
MAX_ATTEMPTS = 6
_RETRY_STATUSES = {429, 502, 503, 504}  # throttled or temporarily unavailable
_HTTP_GONE = 410  # delta link no longer valid
_MAX_DELAY_SECONDS = 120.0

type Json = dict[str, Any]

logger = get_logger(__name__)


@dataclass(frozen=True)
class Pages:
    items: list[Json]
    delta_link: str | None  # set on the last page of a delta query: where the next sync starts


def get_json(
    session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Json:
    """GET and decode JSON, retrying while Graph throttles (Retry-After) or briefly fails."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = session.get(
                url, params=params, headers=headers, timeout=HTTP_TIMEOUT_SECONDS
            )
        except (requests.ConnectionError, requests.Timeout) as error:
            if attempt == MAX_ATTEMPTS:
                raise
            _wait(attempt, None, type(error).__name__)
            continue
        logger.trace("GET %s -> %d", url, response.status_code)
        if response.status_code in _RETRY_STATUSES and attempt < MAX_ATTEMPTS:
            _wait(attempt, response.headers.get("Retry-After"), response.status_code)
            continue
        response.raise_for_status()
        return response.json()
    raise AssertionError("unreachable")


def iter_pages(
    session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Iterator[Json]:
    """Yield each page, following @odata.nextLink (which already carries the query)."""
    next_url: str | None = url
    while next_url:
        page = get_json(session, next_url, params, headers)
        yield page
        next_url, params = page.get("@odata.nextLink"), None


def get_all_pages(
    session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Pages:
    items: list[Json] = []
    delta_link = None
    for page in iter_pages(session, url, params, headers):
        items.extend(page.get("value", []))
        delta_link = page.get("@odata.deltaLink", delta_link)
    logger.trace("Fetched %d items from %s", len(items), url)
    return Pages(items, delta_link)


def get_delta(
    session: requests.Session,
    url: str,
    params: dict[str, Any] | None,
    delta_link: str | None,
    headers: dict[str, str] | None = None,
) -> Pages:
    """Changes since delta_link, or everything from url + params when there is none.

    Raises CursorExpired when Graph no longer accepts the delta link.
    """
    try:
        if delta_link:
            return get_all_pages(session, delta_link, None, headers)
        return get_all_pages(session, url, params, headers)
    except requests.HTTPError as error:
        if delta_link and is_expired_delta(error):
            raise CursorExpired(url) from error
        raise


def is_expired_delta(error: requests.HTTPError) -> bool:
    """410 Gone, or a 4xx naming the sync state (Graph: 'error codes such as syncStateNotFound')."""
    response = error.response
    if response is None:
        return False
    if response.status_code == _HTTP_GONE:
        return True
    return 400 <= response.status_code < 500 and "syncstate" in response.text.lower()


def _wait(attempt: int, retry_after: str | None, cause: object) -> None:
    delay = float(retry_after) if retry_after and retry_after.isdigit() else 2.0**attempt
    delay = min(delay, _MAX_DELAY_SECONDS)
    logger.debug("Graph call failed (%s); retry %d in %.0fs", cause, attempt, delay)
    time.sleep(delay)

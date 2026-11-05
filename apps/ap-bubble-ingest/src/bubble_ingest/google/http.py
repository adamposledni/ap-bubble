"""Plain-HTTP helpers shared by the Google API clients."""

from typing import Any

from google.auth.transport.requests import AuthorizedSession

from bubble_core.log import get_logger

HTTP_TIMEOUT_SECONDS = 30

type Json = dict[str, Any]

logger = get_logger(__name__)


def get_json(session: AuthorizedSession, url: str, params: dict[str, Any] | None = None) -> Json:
    """GET and decode JSON; raises requests.HTTPError on an error status."""
    response = session.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
    logger.trace("GET %s -> %d", url, response.status_code)
    response.raise_for_status()
    return response.json()


def get_all_pages(
    session: AuthorizedSession, url: str, params: dict[str, Any], items_key: str = "items"
) -> tuple[list[Json], Json]:
    """Follow nextPageToken; return all items and the last page (it holds e.g. nextSyncToken)."""
    items: list[Json] = []
    params = dict(params)
    while True:
        page = get_json(session, url, params)
        items.extend(page.get(items_key, []))
        if "nextPageToken" not in page:
            logger.trace("Fetched %d %s from %s", len(items), items_key, url)
            return items, page
        params["pageToken"] = page["nextPageToken"]

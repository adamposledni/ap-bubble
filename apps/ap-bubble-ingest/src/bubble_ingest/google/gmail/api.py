"""Gmail API v1 over plain HTTP: history ids, message ids, mailbox history and messages.

Every call retries with backoff while Gmail rate limits it (see retry.py).
"""

from dataclasses import dataclass

import requests
from google.auth.transport.requests import AuthorizedSession

from bubble_core.log import get_logger
from bubble_ingest.google.gmail.retry import with_retry
from bubble_ingest.google.http import Json, get_all_pages, get_json
from bubble_ingest.l0_sync import CursorExpired

BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"
_PAGE_SIZE = 500  # API maximum
_HISTORY_TYPES = ["messageAdded", "messageDeleted", "labelAdded", "labelRemoved"]
_HTTP_NOT_FOUND = 404  # message deleted, or start history id too old

logger = get_logger(__name__)


@dataclass(frozen=True)
class History:
    records: list[Json]
    history_id: str  # the mailbox's current history id: where the next sync starts


def current_history_id(session: AuthorizedSession) -> str:
    profile = with_retry(lambda: get_json(session, f"{BASE_URL}/profile"))
    logger.debug("Mailbox history id is %s", profile["historyId"])
    return profile["historyId"]


def list_message_ids(session: AuthorizedSession, query: str) -> list[str]:
    """Ids of the messages matching a Gmail search query, without spam and trash."""
    params = {"q": query, "maxResults": _PAGE_SIZE, "includeSpamTrash": "false"}
    url = f"{BASE_URL}/messages"
    messages, _ = with_retry(lambda: get_all_pages(session, url, params, "messages"))
    logger.debug("Listed %d messages", len(messages))
    return [message["id"] for message in messages]


def list_history(session: AuthorizedSession, start_history_id: str) -> History:
    """Mailbox changes after start_history_id; CursorExpired when Gmail no longer keeps them."""
    params = {
        "startHistoryId": start_history_id,
        "historyTypes": _HISTORY_TYPES,  # sent as repeated parameters
        "maxResults": _PAGE_SIZE,
    }
    url = f"{BASE_URL}/history"
    try:
        records, last_page = with_retry(lambda: get_all_pages(session, url, params, "history"))
    except requests.HTTPError as error:
        if _is_not_found(error):
            raise CursorExpired(f"gmail history {start_history_id}") from error
        raise
    logger.debug("Fetched %d history records", len(records))
    return History(records, last_page["historyId"])


def get_message(session: AuthorizedSession, message_id: str) -> Json | None:
    """The full message (headers and parts; attachments only by id), None if it is gone."""
    url = f"{BASE_URL}/messages/{message_id}"
    try:
        return with_retry(lambda: get_json(session, url, {"format": "full"}))
    except requests.HTTPError as error:
        if _is_not_found(error):
            logger.debug("Message %s no longer exists", message_id)
            return None
        raise


def _is_not_found(error: requests.HTTPError) -> bool:
    return error.response is not None and error.response.status_code == _HTTP_NOT_FOUND

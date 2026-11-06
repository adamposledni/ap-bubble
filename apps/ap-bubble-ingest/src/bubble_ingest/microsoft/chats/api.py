"""Teams chats and their messages over Microsoft Graph v1.0 (delegated Chat.Read).

Graph has no delegated delta for chat messages (chats/getAllMessages/delta is application-only),
so messages are listed chat by chat, filtered by lastModifiedDateTime.
"""

from collections.abc import Iterator

import requests

from bubble_core.log import get_logger
from bubble_ingest.microsoft.graph import GRAPH_URL, Json, get_all_pages, get_json, iter_pages

CHATS_URL = f"{GRAPH_URL}/me/chats"
PAGE_SIZE = 50  # API maximum, for chats and for chat messages
# Without it Graph reports systemEventMessage, and newer chat types, as unknownFutureValue.
PREFER_ALL_ENUMS = {"Prefer": "include-unknown-enum-members"}

logger = get_logger(__name__)


def my_user_id(session: requests.Session) -> str:
    return get_json(session, f"{GRAPH_URL}/me", {"$select": "id"})["id"]


def iter_chats_by_last_message(session: requests.Session) -> Iterator[Json]:
    """The user's chats, the latest last message first; pages are fetched as they are consumed.

    Each chat comes with its members (Graph expands about 25 at most) and lastMessagePreview.
    Chats without messages have no preview; Graph sorts them among the old chats.
    """
    params = {
        "$top": PAGE_SIZE,
        "$expand": "members,lastMessagePreview",
        "$orderby": "lastMessagePreview/createdDateTime desc",
    }
    for page in iter_pages(session, CHATS_URL, params, PREFER_ALL_ENUMS):
        chats = page.get("value", [])
        logger.trace("Fetched a page of %d chats", len(chats))
        yield from chats


def list_messages(session: requests.Session, chat_id: str, modified_after: str) -> list[Json]:
    """Messages of the chat created or changed after modified_after, each once, latest change first.

    Soft-deleted messages (deletedDateTime set) and system event messages are included. Graph
    applies the filter only when $orderby names the same property, and only in descending order.
    """
    params = {
        "$top": PAGE_SIZE,
        "$orderby": "lastModifiedDateTime desc",
        "$filter": f"lastModifiedDateTime gt {modified_after}",
    }
    url = f"{CHATS_URL}/{chat_id}/messages"
    messages = _latest_versions(get_all_pages(session, url, params, PREFER_ALL_ENUMS).items)
    logger.debug("Fetched %d messages of chat %s since %s", len(messages), chat_id, modified_after)
    return messages


def _latest_versions(messages: list[Json]) -> list[Json]:
    """Each message once: paging returns a message twice when messages change meanwhile.

    The first occurrence is the latest version, as messages come latest change first.
    """
    latest: dict[str, Json] = {}
    for message in messages:
        latest.setdefault(message["id"], message)
    logger.trace("Dropped %d repeated messages", len(messages) - len(latest))
    return list(latest.values())

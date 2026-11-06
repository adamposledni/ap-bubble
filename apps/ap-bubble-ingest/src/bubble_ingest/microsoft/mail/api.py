"""Microsoft Graph v1.0 for Outlook mail: mail folders, and message changes per folder (delta)."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import requests

from bubble_core.log import get_logger
from bubble_ingest.l0_sync import CursorExpired
from bubble_ingest.microsoft.graph import (
    GRAPH_URL,
    Json,
    get_all_pages,
    get_json,
    is_expired_delta,
    iter_pages,
)

FOLDERS_URL = f"{GRAPH_URL}/me/mailFolders"
PAGE_SIZE = 100
FILTER_CAP = 5000  # most messages a delta with $filter returns (Graph docs)
_FOLDER_FIELDS = "id,displayName,parentFolderId,childFolderCount"  # no counts: they change often
_MESSAGE_FIELDS = ",".join(
    [
        "subject",
        "from",
        "toRecipients",
        "ccRecipients",
        "bccRecipients",
        "receivedDateTime",
        "sentDateTime",
        "body",
        "conversationId",
        "categories",
        "flag",
        "isRead",
        "importance",
        "inferenceClassification",
        "hasAttachments",
        "internetMessageId",
        "parentFolderId",
    ]
)
# Preferences apply per request, so every page sends them; one header, comma-separated (RFC 7240).
_DELTA_HEADERS = {
    "Prefer": ", ".join(
        [
            'outlook.body-content-type="text"',
            'IdType="ImmutableId"',  # a message keeps its id when moved to another folder
            f"odata.maxpagesize={PAGE_SIZE}",
        ]
    )
}
_HTTP_NOT_FOUND = 404

logger = get_logger(__name__)


@dataclass(frozen=True)
class MessagePage:
    entries: list[Json]  # changed messages and @removed entries
    delta_link: str | None  # set on the last page: where the folder's next sync starts


def well_known_folder_id(session: requests.Session, name: str) -> str | None:
    """Id of a well-known folder (e.g. 'deleteditems'); None when the mailbox has none."""
    try:
        folder = get_json(session, f"{FOLDERS_URL}/{name}", {"$select": "id"})
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == _HTTP_NOT_FOUND:
            logger.debug("Mailbox has no %s folder", name)
            return None
        raise
    return folder["id"]


def list_folders(session: requests.Session, parent_id: str | None) -> list[Json]:
    """Folders right under parent_id, or under the top of the mailbox; hidden ones left out."""
    url = f"{FOLDERS_URL}/{parent_id}/childFolders" if parent_id else FOLDERS_URL
    folders = get_all_pages(session, url, {"$select": _FOLDER_FIELDS, "$top": PAGE_SIZE}).items
    logger.trace("%d folders under %s", len(folders), parent_id or "the top")
    return folders


def iter_message_pages(
    session: requests.Session,
    folder_id: str,
    delta_link: str | None,
    received_filter: str | None,
) -> Iterator[MessagePage]:
    """A folder's message changes page by page: since delta_link, or all messages when None.

    received_filter narrows a first load; its links keep it for later rounds.
    Raises CursorExpired when Graph no longer accepts the delta link.
    """
    url, params = delta_link or f"{FOLDERS_URL}/{folder_id}/messages/delta", None
    if not delta_link:
        params = _first_load_params(received_filter)
    try:
        for page in iter_pages(session, url, params, _DELTA_HEADERS):
            yield MessagePage(page.get("value", []), page.get("@odata.deltaLink"))
    except requests.HTTPError as error:
        if delta_link and is_expired_delta(error):
            raise CursorExpired(folder_id) from error
        raise


def _first_load_params(received_filter: str | None) -> dict[str, Any]:
    params = {"$select": _MESSAGE_FIELDS}
    if received_filter:
        params["$filter"] = received_filter
    return params

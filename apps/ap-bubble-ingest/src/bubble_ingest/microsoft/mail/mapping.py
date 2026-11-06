"""Maps Outlook mail folders and messages (Microsoft Graph v1.0) onto L0 items."""

from bubble_core.clock import to_utc
from bubble_core.items import Item
from bubble_ingest.l0_sync import CONTAINER_LIST_ID
from bubble_ingest.microsoft.graph import Json

SOURCE = "outlook_mail"
KIND = "mail"
FOLDER_KIND = "mailfolder"
# Changes with any property, also ones not selected; kept, it would turn those into changes.
_VOLATILE_KEY = "@odata.etag"


def folder_to_item(folder: Json) -> Item:
    return Item(
        source=SOURCE,
        container_id=CONTAINER_LIST_ID,
        external_id=folder["id"],
        kind=FOLDER_KIND,
        title=folder.get("displayName"),
        starts_at=None,
        ends_at=None,
        deleted=False,
        payload=folder,
    )


def to_item(folder_id: str, message: Json) -> Item:
    received = message.get("receivedDateTime")
    return Item(
        source=SOURCE,
        container_id=folder_id,
        external_id=message["id"],
        kind=KIND,
        title=message.get("subject"),
        starts_at=to_utc(received) if received else None,
        ends_at=None,
        deleted=False,
        payload={key: value for key, value in message.items() if key != _VOLATILE_KEY},
    )


def is_removed(entry: Json) -> bool:
    """True for a delta entry saying the message was deleted or moved out of the folder."""
    return "@removed" in entry

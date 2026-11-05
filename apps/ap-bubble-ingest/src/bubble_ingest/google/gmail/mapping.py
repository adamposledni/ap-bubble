"""Maps Gmail messages (format=full) onto L0 items."""

from datetime import UTC, datetime
from typing import Any

from bubble_core.items import Item
from bubble_ingest.google.http import Json

SOURCE = "gmail"
KIND = "mail"
CONTAINER_ID = ""  # one mailbox per account
# Gmail issues new attachment ids on every fetch; kept, they would make every refetch a change.
# A part is still found by partId; fetch the message again for a current attachment id.
_VOLATILE_KEY = "attachmentId"


def to_item(message: Json) -> Item:
    return Item(
        source=SOURCE,
        container_id=CONTAINER_ID,
        external_id=message["id"],
        kind=KIND,
        title=_header(message, "Subject"),
        starts_at=_from_epoch_ms(message["internalDate"]),
        ends_at=None,
        deleted=False,
        payload=_stable(message),
    )


def _stable(value: Any) -> Any:
    """Copy of the value without the keys Gmail changes on every fetch."""
    if isinstance(value, dict):
        return {key: _stable(item) for key, item in value.items() if key != _VOLATILE_KEY}
    if isinstance(value, list):
        return [_stable(item) for item in value]
    return value


def _header(message: Json, name: str) -> str | None:
    """Value of a top-level header; header names are case-insensitive."""
    for header in message.get("payload", {}).get("headers", []):
        if header.get("name", "").lower() == name.lower():
            return header.get("value")
    return None


def _from_epoch_ms(epoch_ms: str) -> str:
    """Gmail's internalDate (epoch ms, as a string) in the vault's timestamp form."""
    return datetime.fromtimestamp(int(epoch_ms) / 1000, UTC).isoformat(timespec="seconds")

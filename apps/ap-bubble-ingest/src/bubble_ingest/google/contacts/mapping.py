"""Maps Google People API persons (contacts and other contacts) onto L0 items."""

from typing import Any

from bubble_core.items import Item

SOURCE = "google_contacts"
KIND = "contact"


def to_item(container_id: str, person: dict[str, Any]) -> Item:
    return Item(
        source=SOURCE,
        container_id=container_id,
        external_id=person["resourceName"],
        kind=KIND,
        title=_title_of(person),
        starts_at=None,  # birthdays and other dates stay in the payload
        ends_at=None,
        deleted=bool(person.get("metadata", {}).get("deleted")),
        payload=person,
    )


def _title_of(person: dict[str, Any]) -> str | None:
    """The display name, else the email address; None for deletion stubs and empty contacts."""
    name = _primary(person.get("names"), "displayName")
    return name or _primary(person.get("emailAddresses"), "value")


def _primary(entries: list[dict[str, Any]] | None, key: str) -> str | None:
    """Value of the entry Google marks as primary, else of the first entry."""
    if not entries:
        return None
    entry = next((e for e in entries if e.get("metadata", {}).get("primary")), entries[0])
    return entry.get(key)

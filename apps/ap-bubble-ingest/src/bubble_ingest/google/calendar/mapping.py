"""Maps Google Calendar events onto L0 items."""

from typing import Any

from bubble_core.clock import to_utc
from bubble_core.items import Item
from bubble_ingest.l0_sync import CONTAINER_LIST_ID

SOURCE = "google_calendar"
KIND = "event"
CALENDAR_KIND = "calendar"


def calendar_to_item(calendar: dict[str, Any]) -> Item:
    return Item(
        source=SOURCE,
        container_id=CONTAINER_LIST_ID,
        external_id=calendar["id"],
        kind=CALENDAR_KIND,
        title=calendar.get("summaryOverride") or calendar.get("summary"),
        starts_at=None,
        ends_at=None,
        deleted=False,
        payload=calendar,
    )


def to_item(calendar_id: str, event: dict[str, Any]) -> Item:
    return Item(
        source=SOURCE,
        container_id=calendar_id,
        external_id=event["id"],
        kind=KIND,
        title=event.get("summary"),
        starts_at=_time_of(event.get("start")),
        ends_at=_time_of(event.get("end")),
        deleted=event.get("status") == "cancelled",
        payload=event,
    )


def _time_of(when: dict[str, str] | None) -> str | None:
    """UTC timestamp of a timed event, or the plain date of an all-day one."""
    if not when:
        return None
    if "dateTime" in when:
        return to_utc(when["dateTime"])
    return when.get("date")

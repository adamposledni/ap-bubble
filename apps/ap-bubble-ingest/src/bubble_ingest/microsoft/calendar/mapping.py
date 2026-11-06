"""Maps Outlook calendars and calendar-view events (times in UTC) onto L0 items."""

from datetime import datetime

from bubble_core.clock import to_utc
from bubble_core.items import Item
from bubble_ingest.l0_sync import CONTAINER_LIST_ID
from bubble_ingest.microsoft.graph import Json

SOURCE = "outlook_calendar"
KIND = "event"
CALENDAR_KIND = "calendar"
_UTC = "UTC"  # the zone requested with Prefer: outlook.timezone


def calendar_to_item(calendar: Json) -> Item:
    return Item(
        source=SOURCE,
        container_id=CONTAINER_LIST_ID,
        external_id=calendar["id"],
        kind=CALENDAR_KIND,
        title=calendar.get("name"),
        starts_at=None,
        ends_at=None,
        deleted=False,
        payload=calendar,
    )


def to_item(calendar_id: str, event: Json) -> Item:
    """An event, occurrence or exception; a delta's @removed entry becomes a deletion."""
    all_day = bool(event.get("isAllDay"))
    return Item(
        source=SOURCE,
        container_id=calendar_id,
        external_id=event["id"],
        kind=KIND,
        title=event.get("subject"),
        starts_at=_time_of(event.get("start"), all_day),
        ends_at=_time_of(event.get("end"), all_day),
        deleted="@removed" in event or bool(event.get("isCancelled")),
        payload=event,
    )


def _time_of(when: Json | None, all_day: bool) -> str | None:
    """UTC timestamp of a timed event, or the plain date of an all-day one (end exclusive).

    Graph sends a dateTime without offset, in the requested zone; all-day events span
    midnight to midnight, so their date part is the day.
    """
    if not when:
        return None
    if when.get("timeZone") != _UTC:
        raise ValueError(f"Expected event times in UTC, got {when.get('timeZone')}")
    if all_day:
        return datetime.fromisoformat(when["dateTime"]).date().isoformat()
    return to_utc(f"{when['dateTime']}+00:00")

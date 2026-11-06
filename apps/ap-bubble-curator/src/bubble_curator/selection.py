"""Which L0 items go to Claude: no noise, and only recent ones (open tasks and contacts always).

Noise rules are deterministic: deleted items, containers (calendars, lists, chats, folders),
Teams system messages, Outlook series masters (their occurrences are items of their own),
promotions and newsletters, events of skipped calendars (holidays, shifts) and service contacts
(no email and no real phone number, e.g. 112).
"""

from datetime import UTC, datetime, timedelta

from bubble_curator.changes import ChangedItem
from bubble_curator.settings import MIN_PHONE_DIGITS, SKIPPED_CALENDAR_PATTERNS

CONTAINER_KINDS = {"calendar", "tasklist", "plan", "chat", "mailfolder"}
_GMAIL_BULK_LABELS = {
    "CATEGORY_PROMOTIONS",
    "CATEGORY_SOCIAL",
    "CATEGORY_UPDATES",
    "CATEGORY_FORUMS",
}
_TASK_TIME_FIELDS = ("updated", "lastModifiedDateTime", "completedDateTime", "createdDateTime")


def window_start(days: int) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat(timespec="seconds")


def is_curatable(item: ChangedItem, since: str) -> bool:
    return not is_noise(item) and in_window(item, since)


def is_noise(item: ChangedItem) -> bool:
    if item.deleted or item.kind in CONTAINER_KINDS:
        return True
    if _is_skipped_calendar_event(item) or _is_service_contact(item):
        return True
    payload = item.payload
    if item.kind == "chat_message":
        return payload.get("messageType") == "systemEventMessage"
    if item.source == "outlook_calendar":
        return payload.get("type") == "seriesMaster"
    if item.source == "outlook_mail":
        return payload.get("inferenceClassification") == "other"
    if item.source == "gmail":
        return bool(_GMAIL_BULK_LABELS & set(payload.get("labelIds", []))) or _has_unsubscribe(item)
    return False


def _is_skipped_calendar_event(item: ChangedItem) -> bool:
    return item.kind == "event" and any(p in item.container_id for p in SKIPPED_CALENDAR_PATTERNS)


def _is_service_contact(item: ChangedItem) -> bool:
    """A contact without an email and without a real phone number (e.g. '155', '*77')."""
    if item.kind != "contact":
        return False
    payload = item.payload
    has_email = any(e.get("value") for e in payload.get("emailAddresses") or [])
    has_phone = any(
        _digit_count(e.get("value")) > MIN_PHONE_DIGITS for e in payload.get("phoneNumbers") or []
    )
    return not has_email and not has_phone


def _digit_count(value: object) -> int:
    return sum(ch.isdigit() for ch in str(value or ""))


def in_window(item: ChangedItem, since: str) -> bool:
    """Recent enough; events count by their end, so upcoming ones are always in."""
    if item.kind == "contact":
        return True
    if item.kind == "task":
        return _is_open_task(item) or _task_time(item) >= since
    return (item.ends_at or item.starts_at or "") >= since


def _has_unsubscribe(item: ChangedItem) -> bool:
    headers = item.payload.get("payload", {}).get("headers", [])
    return any(header.get("name", "").lower() == "list-unsubscribe" for header in headers)


def _is_open_task(item: ChangedItem) -> bool:
    payload = item.payload
    if item.source == "planner":
        return (payload.get("percentComplete") or 0) < 100
    return payload.get("status") not in ("completed",)


def _task_time(item: ChangedItem) -> str:
    """The newest timestamp a task carries (sources name it differently)."""
    times = [str(item.payload[f]) for f in _TASK_TIME_FIELDS if item.payload.get(f)]
    return max(times, default=item.starts_at or "")

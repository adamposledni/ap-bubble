"""Which L0 items go to Claude: no noise, and only recent ones (open tasks and contacts always).

Noise rules are deterministic: deleted items, containers (calendars, lists, chats, folders),
Teams system messages, Outlook series masters (their occurrences are items of their own),
promotions and newsletters.
"""

from datetime import UTC, datetime, timedelta

from bubble_curator.changes import ChangedItem

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

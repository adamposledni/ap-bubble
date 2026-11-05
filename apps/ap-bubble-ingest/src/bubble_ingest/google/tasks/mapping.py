"""Maps Google Tasks onto L0 items."""

from typing import Any

from bubble_core.items import Item

SOURCE = "google_tasks"
KIND = "task"


def to_item(tasklist_id: str, task: dict[str, Any]) -> Item:
    return Item(
        source=SOURCE,
        container_id=tasklist_id,
        external_id=task["id"],
        kind=KIND,
        title=task.get("title"),
        starts_at=_due_date(task.get("due")),
        ends_at=None,
        deleted=bool(task.get("deleted", False)),
        payload=task,
    )


def _due_date(due: str | None) -> str | None:
    """The due date as YYYY-MM-DD: the API keeps only the date part of the RFC 3339 timestamp."""
    return due[:10] if due else None

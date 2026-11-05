"""Maps Google Tasks onto L0 items."""

from typing import Any

from bubble_core.items import Item
from bubble_ingest.l0_sync import CONTAINER_LIST_ID

SOURCE = "google_tasks"
KIND = "task"
TASKLIST_KIND = "tasklist"


def tasklist_to_item(tasklist: dict[str, Any]) -> Item:
    return Item(
        source=SOURCE,
        container_id=CONTAINER_LIST_ID,
        external_id=tasklist["id"],
        kind=TASKLIST_KIND,
        title=tasklist.get("title"),
        starts_at=None,
        ends_at=None,
        deleted=False,
        payload=tasklist,
    )


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

"""Maps To Do task lists and tasks onto L0 items."""

from typing import Any

from bubble_core.items import Item
from bubble_ingest.l0_sync import CONTAINER_LIST_ID
from bubble_ingest.microsoft.due_dates import day_of_date_time_zone

SOURCE = "microsoft_todo"
KIND = "task"
TASKLIST_KIND = "tasklist"


def tasklist_to_item(tasklist: dict[str, Any]) -> Item:
    return Item(
        source=SOURCE,
        container_id=CONTAINER_LIST_ID,
        external_id=tasklist["id"],
        kind=TASKLIST_KIND,
        title=tasklist.get("displayName"),
        starts_at=None,
        ends_at=None,
        deleted=False,
        payload=tasklist,
    )


def to_item(tasklist_id: str, task: dict[str, Any]) -> Item:
    """A task, or its removal (delta sends only id and @removed); due is the day it is due."""
    return Item(
        source=SOURCE,
        container_id=tasklist_id,
        external_id=task["id"],
        kind=KIND,
        title=task.get("title"),
        starts_at=day_of_date_time_zone(task.get("dueDateTime")),
        ends_at=None,
        deleted="@removed" in task,
        payload=task,
    )

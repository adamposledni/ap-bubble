"""Maps Planner plans and tasks onto L0 items."""

from typing import Any

from bubble_core.items import Item
from bubble_ingest.l0_sync import CONTAINER_LIST_ID
from bubble_ingest.microsoft.due_dates import day_of_timestamp

SOURCE = "planner"
KIND = "task"
PLAN_KIND = "plan"


def plan_to_item(plan: dict[str, Any]) -> Item:
    return Item(
        source=SOURCE,
        container_id=CONTAINER_LIST_ID,
        external_id=plan["id"],
        kind=PLAN_KIND,
        title=plan.get("title"),
        starts_at=None,
        ends_at=None,
        deleted=False,
        payload=plan,
    )


def to_item(task: dict[str, Any]) -> Item:
    """A task, in the container of its plan; the due date is the day it is due."""
    return Item(
        source=SOURCE,
        container_id=task["planId"],
        external_id=task["id"],
        kind=KIND,
        title=task.get("title"),
        starts_at=day_of_timestamp(task.get("dueDateTime")),
        ends_at=None,
        deleted=False,
        payload=task,
    )

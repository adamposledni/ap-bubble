"""Open Microsoft To Do tasks (not completed), listed under their list; checklists left out."""

import sqlite3
from typing import Any

from bubble_core.log import get_logger
from bubble_core.queries.open_task import OpenTask, open_task_rows

_SOURCE = "microsoft_todo"
_OPEN = "coalesce(json_extract(t.payload, '$.status'), '') <> 'completed'"

logger = get_logger(__name__)


def todo_open_tasks(conn: sqlite3.Connection) -> list[OpenTask]:
    tasks = [
        OpenTask(
            id=task.id,
            list_name=task.list_name,
            title=task.payload.get("title"),
            notes=_notes(task.payload.get("body")),
            due=task.due,
        )
        for task in open_task_rows(conn, _SOURCE, "tasklist", _OPEN)
    ]
    logger.debug("%d open To Do tasks", len(tasks))
    return tasks


def _notes(body: dict[str, Any] | None) -> str | None:
    """The body when it is non-empty plain text."""
    if not body or body.get("contentType") != "text":
        return None
    return (body.get("content") or "").strip() or None

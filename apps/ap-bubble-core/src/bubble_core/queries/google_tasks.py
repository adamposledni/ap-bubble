"""Open Google Tasks: by due date (none last), each with its open subtasks."""

import sqlite3

from bubble_core.log import get_logger
from bubble_core.queries.open_task import ListKey, OpenTask, TaskRow, open_task_rows

_SOURCE = "google_tasks"
_OPEN = "json_extract(t.payload, '$.status') = 'needsAction'"

logger = get_logger(__name__)


def google_open_tasks(conn: sqlite3.Connection) -> list[OpenTask]:
    tasks = open_task_rows(conn, _SOURCE, "tasklist", _OPEN)
    open_ids = {(t.list_key, t.external_id) for t in tasks}
    children: dict[tuple[ListKey, str], list[TaskRow]] = {}
    top: list[TaskRow] = []
    for task in tasks:
        parent = task.payload.get("parent")
        if parent and (task.list_key, parent) in open_ids:
            children.setdefault((task.list_key, parent), []).append(task)
        else:
            top.append(task)
    top.sort(key=lambda t: (t.due is None, t.due or "", _position(t)))
    logger.debug("%d open Google tasks, %d at top level", len(tasks), len(top))
    return [_to_open(task, children) for task in top]


def _to_open(task: TaskRow, children: dict[tuple[ListKey, str], list[TaskRow]]) -> OpenTask:
    subtasks = sorted(children.get((task.list_key, task.external_id), []), key=_position)
    return OpenTask(
        id=task.id,
        list_name=task.list_name,
        context=task.context,
        title=task.payload.get("title"),
        notes=task.payload.get("notes"),
        due=task.due,
        subtasks=[_to_open(sub, children) for sub in subtasks],
    )


def _position(task: TaskRow) -> str:
    return task.payload.get("position", "")

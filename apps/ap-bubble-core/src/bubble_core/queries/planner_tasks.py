"""Open Planner tasks (assigned to me, not 100 % complete), listed under their plan."""

import sqlite3

from bubble_core.log import get_logger
from bubble_core.queries.open_task import OpenTask, open_task_rows

_SOURCE = "planner"
_OPEN = "coalesce(json_extract(t.payload, '$.percentComplete'), 0) < 100"

logger = get_logger(__name__)


def planner_open_tasks(conn: sqlite3.Connection) -> list[OpenTask]:
    """Without notes: the description sits in task details, which are not ingested."""
    tasks = [
        OpenTask(
            id=task.id,
            list_name=task.list_name,
            title=task.payload.get("title"),
            notes=None,
            due=task.due,
        )
        for task in open_task_rows(conn, _SOURCE, "plan", _OPEN)
    ]
    logger.debug("%d open Planner tasks", len(tasks))
    return tasks

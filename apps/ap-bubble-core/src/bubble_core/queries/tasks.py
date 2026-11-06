"""Open tasks of all task sources (Google Tasks, Planner, To Do): by due date, none last."""

import sqlite3

from bubble_core.log import get_logger
from bubble_core.queries.google_tasks import google_open_tasks
from bubble_core.queries.open_task import OpenTask
from bubble_core.queries.planner_tasks import planner_open_tasks
from bubble_core.queries.todo_tasks import todo_open_tasks

__all__ = ["OpenTask", "open_tasks"]

logger = get_logger(__name__)


def open_tasks(conn: sqlite3.Connection) -> list[OpenTask]:
    """Sorted stably, so tasks due the same day keep each source's own order."""
    tasks = [*google_open_tasks(conn), *planner_open_tasks(conn), *todo_open_tasks(conn)]
    tasks.sort(key=lambda task: (task.due is None, task.due or ""))
    logger.debug("%d open tasks", len(tasks))
    return tasks

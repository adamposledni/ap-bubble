import sqlite3
from collections.abc import Callable
from typing import Any

import pytest

from bubble_core.queries.tasks import OpenTask, open_tasks

type SaveTask = Callable[..., None]


@pytest.fixture
def save_task(store_item: Callable[..., None]) -> SaveTask:
    store_item("google_tasks", "tasklist", "", "list", {"title": "Mine"})

    def save_task(task_id: str, due: str | None = None, **payload: Any) -> None:
        fields = {"status": "needsAction", "title": task_id, **payload}
        store_item("google_tasks", "task", "list", task_id, fields, starts_at=due)

    return save_task


def _titles(tasks: list[OpenTask]) -> list[str | None]:
    return [task.title for task in tasks]


def test_open_tasks_by_due_date_without_due_last(
    conn: sqlite3.Connection, save_task: SaveTask
) -> None:
    save_task("someday")
    save_task("later", due="2026-12-01")
    save_task("overdue", due="2026-10-01")
    save_task("done", due="2026-09-01", status="completed")

    tasks = open_tasks(conn)

    assert _titles(tasks) == ["overdue", "later", "someday"]
    assert tasks[0].list_name == "Mine"


def test_subtasks_sit_under_their_open_parent(
    conn: sqlite3.Connection, save_task: SaveTask
) -> None:
    save_task("parent")
    save_task("second", parent="parent", position="2")
    save_task("first", parent="parent", position="1")
    save_task("closed", status="completed")
    save_task("orphan", parent="closed")

    tasks = open_tasks(conn)

    assert set(_titles(tasks)) == {"orphan", "parent"}
    parent = next(task for task in tasks if task.title == "parent")
    assert _titles(parent.subtasks) == ["first", "second"]


def test_tasks_of_removed_lists_are_hidden(conn: sqlite3.Connection, save_task: SaveTask) -> None:
    save_task("gone")
    conn.execute("UPDATE l0_items SET deleted = 1 WHERE kind = 'tasklist'")

    assert open_tasks(conn) == []

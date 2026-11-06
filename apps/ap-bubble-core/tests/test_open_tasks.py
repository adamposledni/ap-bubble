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


@pytest.fixture
def save_planner_task(store_item: Callable[..., None]) -> SaveTask:
    store_item("planner", "plan", "", "plan", {"title": "Project X"})

    def save(task_id: str, due: str | None = None, **payload: Any) -> None:
        fields = {"planId": "plan", "percentComplete": 0, "title": task_id, **payload}
        store_item("planner", "task", "plan", task_id, fields, starts_at=due)

    return save


@pytest.fixture
def save_todo_task(store_item: Callable[..., None]) -> SaveTask:
    store_item("microsoft_todo", "tasklist", "", "todo", {"title": "Flagged email"})

    def save(task_id: str, due: str | None = None, **payload: Any) -> None:
        fields = {"status": "notStarted", "title": task_id, **payload}
        store_item("microsoft_todo", "task", "todo", task_id, fields, starts_at=due)

    return save


def test_open_planner_tasks_are_listed_under_their_plan(
    conn: sqlite3.Connection, save_planner_task: SaveTask
) -> None:
    save_planner_task("started", due="2026-11-10", percentComplete=50)
    save_planner_task("done", percentComplete=100)

    tasks = open_tasks(conn)

    assert _titles(tasks) == ["started"]
    assert (tasks[0].list_name, tasks[0].notes, tasks[0].due) == ("Project X", None, "2026-11-10")
    assert tasks[0].subtasks == []


def test_planner_tasks_of_plans_no_longer_mine_are_hidden(
    conn: sqlite3.Connection, save_planner_task: SaveTask
) -> None:
    save_planner_task("elsewhere")
    conn.execute("UPDATE l0_items SET deleted = 1 WHERE kind = 'plan'")

    assert open_tasks(conn) == []


def test_open_todo_tasks_carry_their_text_body_as_notes(
    conn: sqlite3.Connection, save_todo_task: SaveTask
) -> None:
    save_todo_task("reply", body={"content": " by Friday ", "contentType": "text"})
    save_todo_task("waiting", status="waitingOnOthers", body={"content": "", "contentType": "text"})
    save_todo_task("styled", body={"content": "<p>x</p>", "contentType": "html"})
    save_todo_task("finished", status="completed")

    tasks = {task.title: task for task in open_tasks(conn)}

    assert set(tasks) == {"reply", "waiting", "styled"}
    assert tasks["reply"].list_name == "Flagged email"
    assert [tasks[t].notes for t in ("reply", "waiting", "styled")] == ["by Friday", None, None]


def test_tasks_of_all_sources_are_sorted_by_due_date(
    conn: sqlite3.Connection,
    save_task: SaveTask,
    save_planner_task: SaveTask,
    save_todo_task: SaveTask,
) -> None:
    save_todo_task("todo someday")
    save_task("google later", due="2026-12-01")
    save_planner_task("planner soon", due="2026-11-10")
    save_todo_task("todo overdue", due="2026-10-01")

    assert _titles(open_tasks(conn)) == [
        "todo overdue",
        "planner soon",
        "google later",
        "todo someday",
    ]

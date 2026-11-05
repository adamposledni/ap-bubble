"""Open tasks of all live task lists: by due date (none last), each with its open subtasks."""

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any

from bubble_core.log import get_logger

_SOURCE = "google_tasks"

type ListKey = tuple[int, str]  # (account id, task list id)

logger = get_logger(__name__)


@dataclass(frozen=True)
class OpenTask:
    id: int
    list_name: str | None
    title: str | None
    notes: str | None
    due: str | None  # YYYY-MM-DD
    subtasks: list["OpenTask"] = field(default_factory=list)


@dataclass(frozen=True)
class _Task:
    id: int
    list_key: ListKey
    external_id: str
    due: str | None
    payload: dict[str, Any]


def open_tasks(conn: sqlite3.Connection) -> list[OpenTask]:
    lists = _live_lists(conn)
    tasks = [t for t in _open(conn) if t.list_key in lists]
    open_ids = {(t.list_key, t.external_id) for t in tasks}
    children: dict[tuple[ListKey, str], list[_Task]] = {}
    top: list[_Task] = []
    for task in tasks:
        parent = task.payload.get("parent")
        if parent and (task.list_key, parent) in open_ids:
            children.setdefault((task.list_key, parent), []).append(task)
        else:
            top.append(task)
    top.sort(key=lambda t: (t.due is None, t.due or "", _position(t)))
    logger.debug("%d open tasks, %d at top level", len(tasks), len(top))
    return [_to_open(task, lists, children) for task in top]


def _to_open(
    task: _Task,
    lists: dict[ListKey, str | None],
    children: dict[tuple[ListKey, str], list[_Task]],
) -> OpenTask:
    subtasks = sorted(children.get((task.list_key, task.external_id), []), key=_position)
    return OpenTask(
        id=task.id,
        list_name=lists[task.list_key],
        title=task.payload.get("title"),
        notes=task.payload.get("notes"),
        due=task.due,
        subtasks=[_to_open(sub, lists, children) for sub in subtasks],
    )


def _position(task: _Task) -> str:
    return task.payload.get("position", "")


def _live_lists(conn: sqlite3.Connection) -> dict[ListKey, str | None]:
    rows = conn.execute(
        "SELECT account_id, external_id, title FROM l0_items "
        "WHERE source = ? AND kind = 'tasklist' AND deleted = 0",
        (_SOURCE,),
    ).fetchall()
    return {(row["account_id"], row["external_id"]): row["title"] for row in rows}


def _open(conn: sqlite3.Connection) -> list[_Task]:
    rows = conn.execute(
        "SELECT id, account_id, container_id, external_id, starts_at, payload FROM l0_items "
        "WHERE source = ? AND kind = 'task' AND deleted = 0 "
        "AND json_extract(payload, '$.status') = 'needsAction'",
        (_SOURCE,),
    ).fetchall()
    return [
        _Task(
            id=row["id"],
            list_key=(row["account_id"], row["container_id"]),
            external_id=row["external_id"],
            due=row["starts_at"],
            payload=json.loads(row["payload"]),
        )
        for row in rows
    ]

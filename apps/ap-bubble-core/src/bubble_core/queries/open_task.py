"""The open task every task source is shown as, and the L0 lookup the sources share."""

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any, cast

from bubble_core.accounts import Context
from bubble_core.log import get_logger

type ListKey = tuple[int, str]  # (account id, list id: task list or plan)

logger = get_logger(__name__)


@dataclass(frozen=True)
class OpenTask:
    id: int
    list_name: str | None
    context: Context  # of the task's account: work or personal
    title: str | None
    notes: str | None
    due: str | None  # YYYY-MM-DD
    subtasks: list["OpenTask"] = field(default_factory=list)


@dataclass(frozen=True)
class TaskRow:
    """A live task of a live list, as stored in L0."""

    id: int
    list_key: ListKey
    list_name: str | None
    context: Context
    external_id: str
    due: str | None
    payload: dict[str, Any]


def open_task_rows(
    conn: sqlite3.Connection, source: str, list_kind: str, open_condition: str
) -> list[TaskRow]:
    """Live tasks of the source's live lists for which open_condition (SQL over t) holds."""
    rows = conn.execute(
        "SELECT t.id, t.account_id, t.container_id, t.external_id, t.starts_at, t.payload, "
        "l.title AS list_name, a.context FROM l0_items t "
        "JOIN l0_items l ON l.account_id = t.account_id AND l.source = t.source "
        "AND l.container_id = '' AND l.external_id = t.container_id "
        "AND l.kind = ? AND l.deleted = 0 "
        "JOIN lm_accounts a ON a.id = t.account_id "
        f"WHERE t.source = ? AND t.kind = 'task' AND t.deleted = 0 AND ({open_condition})",
        (list_kind, source),
    ).fetchall()
    logger.trace("%d open %s tasks", len(rows), source)
    return [
        TaskRow(
            id=row["id"],
            list_key=(row["account_id"], row["container_id"]),
            list_name=row["list_name"],
            context=cast(Context, row["context"]),
            external_id=row["external_id"],
            due=row["starts_at"],
            payload=json.loads(row["payload"]),
        )
        for row in rows
    ]

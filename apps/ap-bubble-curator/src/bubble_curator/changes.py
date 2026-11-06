"""Reads the L0 change set after the cursor: rows changed by finished ingest runs, in order."""

import json
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from bubble_core.log import get_logger
from bubble_curator.cursor import Position
from bubble_curator.settings import RUNNING_RUN_TIMEOUT_HOURS

_CHUNK = 500

logger = get_logger(__name__)


@dataclass(frozen=True)
class ChangedItem:
    id: int
    account_id: int
    context: str  # work or personal
    source: str
    kind: str
    container_id: str
    title: str | None
    starts_at: str | None
    ends_at: str | None
    deleted: bool
    payload: dict[str, Any]


@dataclass(frozen=True)
class ChangeSet:
    items: list[ChangedItem]  # the ones kept
    end: Position | None  # the last row looked at; None when there was nothing new
    examined: int


def read_changes(
    conn: sqlite3.Connection,
    after: Position,
    keep: Callable[[ChangedItem], bool],
    max_kept: int,
) -> ChangeSet:
    """Rows after the cursor, up to max_kept kept ones; rows of ingest runs still going wait."""
    ceiling = _first_running_ingest_run(conn)
    kept: list[ChangedItem] = []
    end, examined, position = None, 0, after
    while len(kept) < max_kept:
        rows = _rows_after(conn, position, ceiling)
        for row in rows:
            item, examined = _to_item(row), examined + 1
            end = position = Position(row["changed_run_id"], row["id"])
            if keep(item):
                kept.append(item)
                if len(kept) >= max_kept:
                    break
        if len(rows) < _CHUNK:
            break
    logger.info("Change set: %d rows examined, %d kept, ends at %s", examined, len(kept), end)
    return ChangeSet(kept, end, examined)


def _rows_after(
    conn: sqlite3.Connection, after: Position, ceiling: int | None
) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT i.*, a.context FROM l0_items i JOIN lm_accounts a ON a.id = i.account_id "
        "WHERE (i.changed_run_id, i.id) > (?, ?) AND (? IS NULL OR i.changed_run_id < ?) "
        "ORDER BY i.changed_run_id, i.id LIMIT ?",
        (after.changed_run_id, after.item_id, ceiling, ceiling, _CHUNK),
    ).fetchall()


def _first_running_ingest_run(conn: sqlite3.Connection) -> int | None:
    """Rows of this and later runs are left for later: the run may still add or change rows."""
    alive_since = datetime.now(UTC) - timedelta(hours=RUNNING_RUN_TIMEOUT_HOURS)
    row = conn.execute(
        "SELECT MIN(id) AS id FROM lm_job_runs "
        "WHERE status = 'running' AND job_name LIKE 'ingest.%' AND started_at > ?",
        (alive_since.isoformat(timespec="seconds"),),
    ).fetchone()
    if row["id"] is not None:
        logger.info("Ingest run %d is still running; its changes wait for the next run", row["id"])
    return row["id"]


def _to_item(row: sqlite3.Row) -> ChangedItem:
    return ChangedItem(
        id=row["id"],
        account_id=row["account_id"],
        context=row["context"],
        source=row["source"],
        kind=row["kind"],
        container_id=row["container_id"],
        title=row["title"],
        starts_at=row["starts_at"],
        ends_at=row["ends_at"],
        deleted=bool(row["deleted"]),
        payload=json.loads(row["payload"]),
    )

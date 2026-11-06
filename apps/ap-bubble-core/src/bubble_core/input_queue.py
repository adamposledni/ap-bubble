"""The curator's side of the L1 input queue: take queued inputs, record how curation went."""

import sqlite3

from bubble_core.clock import utc_now
from bubble_core.inputs import Input, Status, get_input
from bubble_core.log import get_logger

logger = get_logger(__name__)


def queued_inputs(conn: sqlite3.Connection, limit: int) -> list[Input]:
    """The oldest queued inputs first."""
    rows = conn.execute(
        "SELECT id FROM l1_inputs WHERE status = 'queued' ORDER BY id LIMIT ?", (limit,)
    ).fetchall()
    return [get_input(conn, row["id"]) for row in rows]


def set_status(
    conn: sqlite3.Connection, input_ids: list[int], status: Status, error: str | None = None
) -> None:
    """Move inputs to a new status; done and failed also record when. Commits."""
    processed_at = utc_now() if status in ("done", "failed") else None
    conn.executemany(
        "UPDATE l1_inputs SET status = ?, error = ?, processed_at = ? WHERE id = ?",
        [(status, error, processed_at, input_id) for input_id in input_ids],
    )
    conn.commit()
    logger.debug("Inputs %s are now %s", input_ids, status)


def requeue_stuck(conn: sqlite3.Connection) -> int:
    """Put inputs left 'processing' by an interrupted run back in the queue. Commits."""
    cursor = conn.execute(
        "UPDATE l1_inputs SET status = 'queued', error = NULL WHERE status = 'processing'"
    )
    conn.commit()
    if cursor.rowcount:
        logger.warning("Requeued %d inputs left processing by an earlier run", cursor.rowcount)
    return cursor.rowcount

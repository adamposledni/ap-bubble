"""Records every job run in lm_job_runs, so it shows up on the audit page."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime

from adams_bubble_core.log import get_logger

logger = get_logger(__name__)


@dataclass
class JobRun:
    id: int
    job_name: str
    scope: str | None
    items_processed: int = 0


@contextmanager
def job_run(conn: sqlite3.Connection, job_name: str, scope: str | None = None) -> Iterator[JobRun]:
    """Record a 'running' row, then mark it succeeded or failed.

    On failure the job's uncommitted work is rolled back and the error is re-raised.
    """
    run = _start(conn, job_name, scope)
    try:
        yield run
    except Exception as exc:
        conn.rollback()
        _finish(conn, run, "failed", repr(exc))
        logger.exception("Job %s [%s] failed (run %d)", job_name, scope, run.id)
        raise
    _finish(conn, run, "succeeded")
    logger.info(
        "Job %s [%s] succeeded (run %d, %d items)", job_name, scope, run.id, run.items_processed
    )


def _start(conn: sqlite3.Connection, job_name: str, scope: str | None) -> JobRun:
    cursor = conn.execute(
        "INSERT INTO lm_job_runs (job_name, scope, status, started_at) VALUES (?, ?, 'running', ?)",
        (job_name, scope, _now()),
    )
    conn.commit()
    run = JobRun(id=cursor.lastrowid or 0, job_name=job_name, scope=scope)
    logger.info("Job %s [%s] started (run %d)", job_name, scope, run.id)
    return run


def _finish(conn: sqlite3.Connection, run: JobRun, status: str, error: str | None = None) -> None:
    conn.execute(
        "UPDATE lm_job_runs SET status = ?, finished_at = ?, items_processed = ?, error = ? "
        "WHERE id = ?",
        (status, _now(), run.items_processed, error, run.id),
    )
    conn.commit()


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")

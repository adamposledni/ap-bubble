"""Monitoring: job states, runs, L0 item counts, the L1 queue, uncurated L0 changes (LM)."""

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from bubble_core.log import get_logger
from bubble_core.queries.job_runs import DRY_RUN_JOB, JobRun, RunningJob, recent_runs, running_jobs

STALE_AFTER = timedelta(hours=24)
_INGEST_PREFIX = "ingest."

logger = get_logger(__name__)


@dataclass(frozen=True)
class JobStatus:
    """The latest run of one job for one scope (e.g. an account)."""

    job_name: str
    scope: str | None
    last_status: str  # running, succeeded, failed
    last_started_at: str
    last_success_at: str | None
    last_error: str | None
    items_in_l0: int | None  # ingest jobs only
    stale: bool  # no success within STALE_AFTER


@dataclass(frozen=True)
class Monitor:
    jobs: list[JobStatus]
    runs: list[JobRun]  # last 7 days, dry runs included
    running: list[RunningJob]
    queue: dict[str, int]  # L1 inputs per status
    changes_waiting: int  # L0 rows past the curator cursor


def monitor(conn: sqlite3.Connection) -> Monitor:
    result = Monitor(
        _job_statuses(conn),
        recent_runs(conn),
        running_jobs(conn),
        _queue_counts(conn),
        _changes_waiting(conn),
    )
    logger.debug(
        "Monitor: %d jobs, %d runs, %d L0 changes waiting",
        len(result.jobs),
        len(result.runs),
        result.changes_waiting,
    )
    return result


def _job_statuses(conn: sqlite3.Connection) -> list[JobStatus]:
    """Latest run per job and scope; dry runs are no job of their own (and never count)."""
    rows = conn.execute(
        "SELECT r.*, (SELECT MAX(s.finished_at) FROM lm_job_runs s WHERE s.job_name = r.job_name "
        "AND s.scope IS r.scope AND s.status = 'succeeded') AS last_success_at "
        "FROM lm_job_runs r WHERE r.job_name != ? AND r.id = (SELECT MAX(x.id) FROM lm_job_runs x "
        "WHERE x.job_name = r.job_name AND x.scope IS r.scope) ORDER BY r.job_name, r.scope",
        (DRY_RUN_JOB,),
    ).fetchall()
    counts = _item_counts(conn)
    stale_before = (datetime.now(UTC) - STALE_AFTER).isoformat(timespec="seconds")
    return [
        JobStatus(
            job_name=row["job_name"],
            scope=row["scope"],
            last_status=row["status"],
            last_started_at=row["started_at"],
            last_success_at=row["last_success_at"],
            last_error=row["error"],
            items_in_l0=_items_of(row["job_name"], row["scope"], counts),
            stale=(row["last_success_at"] or "") < stale_before,
        )
        for row in rows
    ]


def _item_counts(conn: sqlite3.Connection) -> dict[tuple[str, str], int]:
    """Live L0 items per (source, account key)."""
    rows = conn.execute(
        "SELECT i.source, a.provider || ':' || a.email AS account_key, COUNT(*) AS live "
        "FROM l0_items i JOIN lm_accounts a ON a.id = i.account_id "
        "WHERE i.deleted = 0 GROUP BY i.source, account_key"
    ).fetchall()
    return {(row["source"], row["account_key"]): row["live"] for row in rows}


def _queue_counts(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute("SELECT status, COUNT(*) AS n FROM l1_inputs GROUP BY status").fetchall()
    return {row["status"]: row["n"] for row in rows}


def _changes_waiting(conn: sqlite3.Connection) -> int:
    """L0 rows the curator has not looked at yet, in its (changed_run_id, id) order."""
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM l0_items i LEFT JOIN lm_curator_cursor c ON c.id = 1 "
        "WHERE (i.changed_run_id, i.id) > (COALESCE(c.changed_run_id, 0), COALESCE(c.item_id, 0))"
    ).fetchone()
    return row["n"]


def _items_of(job_name: str, scope: str | None, counts: dict[tuple[str, str], int]) -> int | None:
    if not job_name.startswith(_INGEST_PREFIX) or scope is None:
        return None
    return counts.get((job_name.removeprefix(_INGEST_PREFIX), scope), 0)

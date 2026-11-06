"""Monitoring: the state of every job per scope, recent runs, L0 item counts, the L1 queue (LM)."""

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from bubble_core.log import get_logger

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
class JobRun:
    id: int
    job_name: str
    scope: str | None
    status: str
    started_at: str
    duration_seconds: float | None
    items_processed: int
    error: str | None


@dataclass(frozen=True)
class Monitor:
    jobs: list[JobStatus]
    runs: list[JobRun]
    queue: dict[str, int]  # L1 inputs per status


def monitor(conn: sqlite3.Connection, run_limit: int = 50) -> Monitor:
    result = Monitor(_job_statuses(conn), _recent_runs(conn, run_limit), _queue_counts(conn))
    logger.debug("Monitor: %d jobs, %d runs", len(result.jobs), len(result.runs))
    return result


def _job_statuses(conn: sqlite3.Connection) -> list[JobStatus]:
    rows = conn.execute(
        "SELECT r.*, (SELECT MAX(s.finished_at) FROM lm_job_runs s WHERE s.job_name = r.job_name "
        "AND s.scope IS r.scope AND s.status = 'succeeded') AS last_success_at "
        "FROM lm_job_runs r WHERE r.id = (SELECT MAX(x.id) FROM lm_job_runs x "
        "WHERE x.job_name = r.job_name AND x.scope IS r.scope) ORDER BY r.job_name, r.scope"
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


def _recent_runs(conn: sqlite3.Connection, limit: int) -> list[JobRun]:
    rows = conn.execute("SELECT * FROM lm_job_runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [
        JobRun(
            id=row["id"],
            job_name=row["job_name"],
            scope=row["scope"],
            status=row["status"],
            started_at=row["started_at"],
            duration_seconds=_duration(row["started_at"], row["finished_at"]),
            items_processed=row["items_processed"],
            error=row["error"],
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


def _items_of(job_name: str, scope: str | None, counts: dict[tuple[str, str], int]) -> int | None:
    if not job_name.startswith(_INGEST_PREFIX) or scope is None:
        return None
    return counts.get((job_name.removeprefix(_INGEST_PREFIX), scope), 0)


def _duration(started_at: str, finished_at: str | None) -> float | None:
    if finished_at is None:
        return None
    return (
        datetime.fromisoformat(finished_at) - datetime.fromisoformat(started_at)
    ).total_seconds()

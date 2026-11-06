"""Job runs from the LM job log: recent ones, the ones running now, one run with its batches."""

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from bubble_core.curator_runs import BatchInfo, batch_names, batches_of, done_batches
from bubble_core.log import get_logger

CURATOR_JOB = "curator.run"
DRY_RUN_JOB = "curator.dry_run"
RECENT_DAYS = 7
MAX_RUNS = 500
RUNNING_MAX_AGE = timedelta(hours=12)  # an older 'running' row is a crashed run, not a live one

logger = get_logger(__name__)


@dataclass(frozen=True)
class JobRun:
    id: int
    job_name: str  # a dry run is reported as a run of the curator job
    scope: str | None
    status: str
    started_at: str
    finished_at: str | None
    duration_seconds: float | None
    items_processed: int
    error: str | None
    dry_run: bool


@dataclass(frozen=True)
class RunningJob:
    run: JobRun
    batch_current: int | None  # curator only: the batch being curated
    batch_total: int | None


@dataclass(frozen=True)
class RunDetail:
    run: JobRun
    batches: list[BatchInfo]  # curator runs only


def recent_runs(conn: sqlite3.Connection) -> list[JobRun]:
    """Runs of the last RECENT_DAYS days, newest first (capped at MAX_RUNS)."""
    since = _iso_ago(timedelta(days=RECENT_DAYS))
    rows = conn.execute(
        "SELECT * FROM lm_job_runs WHERE started_at >= ? ORDER BY id DESC LIMIT ?",
        (since, MAX_RUNS),
    ).fetchall()
    return [_to_run(row) for row in rows]


def running_jobs(conn: sqlite3.Connection) -> list[RunningJob]:
    since = _iso_ago(RUNNING_MAX_AGE)
    rows = conn.execute(
        "SELECT * FROM lm_job_runs WHERE status = 'running' AND started_at >= ? ORDER BY id",
        (since,),
    ).fetchall()
    return [_running(_to_run(row)) for row in rows]


def run_detail(conn: sqlite3.Connection, run_id: int) -> RunDetail | None:
    row = conn.execute("SELECT * FROM lm_job_runs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        return None
    run = _to_run(row)
    batches = batches_of(run.id, run.status, run.dry_run) if run.job_name == CURATOR_JOB else []
    return RunDetail(run, batches)


def _running(run: JobRun) -> RunningJob:
    if run.job_name != CURATOR_JOB or run.dry_run:
        return RunningJob(run, None, None)
    total = len(batch_names(run.id))
    return RunningJob(run, done_batches(run.id) + 1 if total else None, total or None)


def _to_run(row: sqlite3.Row) -> JobRun:
    dry_run = row["job_name"] == DRY_RUN_JOB
    return JobRun(
        id=row["id"],
        job_name=CURATOR_JOB if dry_run else row["job_name"],
        scope=row["scope"],
        status=row["status"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        duration_seconds=_duration(row["started_at"], row["finished_at"]),
        items_processed=row["items_processed"],
        error=row["error"],
        dry_run=dry_run,
    )


def _iso_ago(age: timedelta) -> str:
    return (datetime.now(UTC) - age).isoformat(timespec="seconds")


def _duration(started_at: str, finished_at: str | None) -> float | None:
    if finished_at is None:
        return None
    return (
        datetime.fromisoformat(finished_at) - datetime.fromisoformat(started_at)
    ).total_seconds()

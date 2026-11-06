import sqlite3
from collections.abc import Callable

import pytest

from bubble_core.accounts import Account
from bubble_core.inputs import add_input
from bubble_core.job_log import job_run
from bubble_core.queries.monitor import monitor


def _run(conn: sqlite3.Connection, job_name: str, scope: str, fail: bool = False) -> None:
    if not fail:
        with job_run(conn, job_name, scope) as run:
            run.items_processed = 3
        return
    with pytest.raises(RuntimeError), job_run(conn, job_name, scope):
        raise RuntimeError("boom")


def test_latest_run_per_job_and_scope_with_last_success(
    conn: sqlite3.Connection, account: Account
) -> None:
    _run(conn, "ingest.google_tasks", account.key)
    _run(conn, "ingest.google_tasks", account.key, fail=True)

    [job] = monitor(conn).jobs

    assert (job.last_status, job.last_error) == ("failed", "RuntimeError('boom')")
    assert job.last_success_at is not None
    assert not job.stale


def test_job_without_success_is_stale(conn: sqlite3.Connection, account: Account) -> None:
    _run(conn, "ingest.gmail", account.key, fail=True)

    [job] = monitor(conn).jobs

    assert (job.last_success_at, job.stale) == (None, True)


def test_ingest_jobs_report_their_live_l0_items(
    conn: sqlite3.Connection, account: Account, store_item: Callable[..., None]
) -> None:
    _run(conn, "ingest.google_tasks", account.key)
    store_item("google_tasks", "task", "list", "t1", {"title": "a"})
    store_item("google_tasks", "task", "list", "t2", {"title": "b"}, deleted=True)

    jobs = {job.job_name: job for job in monitor(conn).jobs}  # store_item adds a test.job run

    assert jobs["ingest.google_tasks"].items_in_l0 == 1
    assert jobs["test.job"].items_in_l0 is None


def test_recent_runs_newest_first_with_duration(conn: sqlite3.Connection, account: Account) -> None:
    _run(conn, "ingest.gmail", account.key)
    _run(conn, "ingest.google_tasks", account.key)

    runs = monitor(conn).runs

    assert [r.job_name for r in runs] == ["ingest.google_tasks", "ingest.gmail"]
    assert runs[0].duration_seconds is not None and runs[0].items_processed == 3


def test_queue_is_counted_per_status(conn: sqlite3.Connection) -> None:
    add_input(conn, "one", [])
    add_input(conn, "two", [])

    assert monitor(conn).queue == {"queued": 2}

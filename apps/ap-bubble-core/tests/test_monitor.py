import sqlite3
from collections.abc import Callable

import pytest

from bubble_core.accounts import Account
from bubble_core.clock import utc_now
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


def test_dry_run_is_a_curator_run_and_no_job(conn: sqlite3.Connection) -> None:
    with job_run(conn, "curator.dry_run"):
        pass

    result = monitor(conn)

    assert result.jobs == []
    [run] = result.runs
    assert (run.job_name, run.dry_run) == ("curator.run", True)


def test_recent_runs_cover_the_last_seven_days(conn: sqlite3.Connection, account: Account) -> None:
    _run(conn, "ingest.gmail", account.key)
    conn.execute("UPDATE lm_job_runs SET started_at = '2020-01-01T00:00:00+00:00'")
    _run(conn, "ingest.google_tasks", account.key)

    assert [r.job_name for r in monitor(conn).runs] == ["ingest.google_tasks"]


def test_running_job_is_listed_without_batch_progress_for_ingest(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO lm_job_runs (job_name, scope, status, started_at) "
        "VALUES ('ingest.gmail', 'google:me@gmail.com', 'running', ?)",
        (utc_now(),),
    )

    [running] = monitor(conn).running

    assert (running.run.job_name, running.batch_current) == ("ingest.gmail", None)


def test_l0_changes_past_the_curator_cursor_wait(
    conn: sqlite3.Connection, store_item: Callable[..., None]
) -> None:
    store_item("google_tasks", "task", "list", "t1", {"title": "a"})
    store_item("google_tasks", "task", "list", "t2", {"title": "b"})
    assert monitor(conn).changes_waiting == 2

    first = conn.execute("SELECT changed_run_id, id FROM l0_items ORDER BY id").fetchone()
    conn.execute(
        "INSERT INTO lm_curator_cursor (id, changed_run_id, item_id, updated_at) "
        "VALUES (1, ?, ?, ?)",
        (first["changed_run_id"], first["id"], utc_now()),
    )

    assert monitor(conn).changes_waiting == 1

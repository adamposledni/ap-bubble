import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest

from bubble_core.db import open_vault
from bubble_core.job_log import job_run


@pytest.fixture
def conn(vault_path: Path) -> Iterator[sqlite3.Connection]:
    with closing(open_vault(vault_path)) as conn:
        yield conn


def _only_run(conn: sqlite3.Connection) -> sqlite3.Row:
    return conn.execute("SELECT * FROM lm_job_runs").fetchone()


def test_successful_run_is_recorded(conn: sqlite3.Connection) -> None:
    with job_run(conn, "test.job", "account-1") as run:
        run.items_processed = 3

    row = _only_run(conn)
    assert (row["status"], row["scope"], row["items_processed"]) == ("succeeded", "account-1", 3)
    assert row["finished_at"] is not None


def test_failed_run_is_recorded_and_error_reraised(conn: sqlite3.Connection) -> None:
    with pytest.raises(ValueError), job_run(conn, "test.job"):
        raise ValueError("boom")

    row = _only_run(conn)
    assert row["status"] == "failed"
    assert "boom" in row["error"]


def test_failed_run_rolls_back_uncommitted_work(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE TABLE scratch (x INTEGER)")
    conn.commit()

    with pytest.raises(RuntimeError), job_run(conn, "test.job"):
        conn.execute("INSERT INTO scratch VALUES (1)")
        raise RuntimeError("boom")

    assert conn.execute("SELECT COUNT(*) FROM scratch").fetchone()[0] == 0

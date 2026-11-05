import sqlite3
from datetime import UTC, datetime
from typing import Any

import pytest

from bubble_core.accounts import Account
from bubble_ingest.google import auth as google_auth
from bubble_ingest.google.tasks import api
from bubble_ingest.google.tasks.sync import CURSOR_OVERLAP, sync_account


class FakeTasksApi:
    """Serves scripted tasks for every list and records (tasklist_id, updated_min) requests."""

    def __init__(self) -> None:
        self.tasks: list[dict[str, Any]] = []
        self.requests: list[tuple[str, str | None]] = []

    def list_tasks(
        self, session: object, tasklist_id: str, updated_min: str | None
    ) -> list[dict[str, Any]]:
        self.requests.append((tasklist_id, updated_min))
        return list(self.tasks)


@pytest.fixture
def fake_api(monkeypatch: pytest.MonkeyPatch) -> FakeTasksApi:
    fake = FakeTasksApi()
    monkeypatch.setattr(google_auth, "session_for", lambda account_key: object())
    monkeypatch.setattr(api, "list_tasklists", lambda session: [{"id": "list1"}])
    monkeypatch.setattr(api, "list_tasks", fake.list_tasks)
    return fake


def _task(task_id: str, deleted: bool = False) -> dict[str, Any]:
    return {"id": task_id, "status": "needsAction", "deleted": deleted}


def _deleted_flags(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute("SELECT external_id, deleted FROM l0_items").fetchall()
    return {row["external_id"]: row["deleted"] for row in rows}


def _stored_cursor(conn: sqlite3.Connection) -> datetime:
    row = conn.execute("SELECT cursor FROM lm_sync_cursors").fetchone()
    return datetime.fromisoformat(row["cursor"])


def test_first_sync_loads_every_list_fully(
    conn: sqlite3.Connection, account: Account, fake_api: FakeTasksApi
) -> None:
    fake_api.tasks = [_task("t1")]

    sync_account(conn, account)

    assert fake_api.requests == [("list1", None)]
    assert _deleted_flags(conn) == {"t1": 0}


def test_cursor_is_fetch_start_minus_overlap(
    conn: sqlite3.Connection, account: Account, fake_api: FakeTasksApi
) -> None:
    before = datetime.now(UTC).replace(microsecond=0)

    sync_account(conn, account)

    cursor = _stored_cursor(conn)
    assert before - CURSOR_OVERLAP <= cursor <= datetime.now(UTC) - CURSOR_OVERLAP


def test_next_sync_asks_for_tasks_updated_since_cursor(
    conn: sqlite3.Connection, account: Account, fake_api: FakeTasksApi
) -> None:
    sync_account(conn, account)
    cursor = conn.execute("SELECT cursor FROM lm_sync_cursors").fetchone()["cursor"]

    sync_account(conn, account)

    assert fake_api.requests == [("list1", None), ("list1", cursor)]


def test_task_deleted_in_google_is_flagged_deleted(
    conn: sqlite3.Connection, account: Account, fake_api: FakeTasksApi
) -> None:
    fake_api.tasks = [_task("t1"), _task("t2")]
    sync_account(conn, account)
    fake_api.tasks = [_task("t2", deleted=True)]

    sync_account(conn, account)

    assert _deleted_flags(conn) == {"t1": 0, "t2": 1}


def test_sync_is_recorded_as_job_run(
    conn: sqlite3.Connection, account: Account, fake_api: FakeTasksApi
) -> None:
    fake_api.tasks = [_task("t1"), _task("t2")]

    sync_account(conn, account)

    row = conn.execute("SELECT * FROM lm_job_runs").fetchone()
    assert (row["job_name"], row["scope"], row["status"], row["items_processed"]) == (
        "ingest.google_tasks",
        "google:me@gmail.com",
        "succeeded",
        2,
    )

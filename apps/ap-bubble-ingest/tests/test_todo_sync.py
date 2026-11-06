import sqlite3
from typing import Any

import pytest

from bubble_core.accounts import Account, upsert_account
from bubble_ingest.l0_sync import CursorExpired
from bubble_ingest.microsoft import auth as microsoft_auth
from bubble_ingest.microsoft.todo import api
from bubble_ingest.microsoft.todo.api import TaskChanges
from bubble_ingest.microsoft.todo.sync import sync_account


class FakeTodoApi:
    """Serves scripted tasks with numbered delta links; records (list id, delta link) calls."""

    def __init__(self) -> None:
        self.tasks: list[dict[str, Any]] = []
        self.calls: list[tuple[str, str | None]] = []
        self.expired = False

    def task_changes(self, session: object, tasklist_id: str, delta_link: str | None):
        self.calls.append((tasklist_id, delta_link))
        if delta_link and self.expired:
            raise CursorExpired(tasklist_id)
        return TaskChanges(list(self.tasks), f"https://delta/{len(self.calls)}")


@pytest.fixture
def fake_api(monkeypatch: pytest.MonkeyPatch) -> FakeTodoApi:
    fake = FakeTodoApi()
    monkeypatch.setattr(microsoft_auth, "session_for", lambda account_key: object())
    tasklists = [{"id": "list1", "displayName": "Tasks", "wellknownListName": "defaultList"}]
    monkeypatch.setattr(api, "list_tasklists", lambda session: tasklists)
    monkeypatch.setattr(api, "task_changes", fake.task_changes)
    return fake


@pytest.fixture
def work_account(conn: sqlite3.Connection) -> Account:
    return upsert_account(conn, "microsoft", "me@work.example", "work")


def _task(task_id: str) -> dict[str, Any]:
    return {"id": task_id, "title": task_id, "status": "notStarted"}


def _removed(task_id: str) -> dict[str, Any]:
    return {"id": task_id, "@removed": {"reason": "deleted"}}


def _deleted_flags(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute("SELECT external_id, deleted FROM l0_items WHERE kind = 'task'").fetchall()
    return {row["external_id"]: row["deleted"] for row in rows}


def test_first_sync_loads_every_list_fully(
    conn: sqlite3.Connection, work_account: Account, fake_api: FakeTodoApi
) -> None:
    fake_api.tasks = [_task("t1")]

    sync_account(conn, work_account)

    assert fake_api.calls == [("list1", None)]
    assert _deleted_flags(conn) == {"t1": 0}


def test_next_sync_follows_the_stored_delta_link(
    conn: sqlite3.Connection, work_account: Account, fake_api: FakeTodoApi
) -> None:
    sync_account(conn, work_account)

    sync_account(conn, work_account)

    assert fake_api.calls == [("list1", None), ("list1", "https://delta/1")]
    cursor = conn.execute("SELECT cursor FROM lm_sync_cursors").fetchone()["cursor"]
    assert cursor == "https://delta/2"


def test_removed_task_is_flagged_deleted(
    conn: sqlite3.Connection, work_account: Account, fake_api: FakeTodoApi
) -> None:
    fake_api.tasks = [_task("t1"), _task("t2")]
    sync_account(conn, work_account)
    fake_api.tasks = [_removed("t2")]

    sync_account(conn, work_account)

    assert _deleted_flags(conn) == {"t1": 0, "t2": 1}


def test_expired_delta_link_falls_back_to_a_full_load(
    conn: sqlite3.Connection, work_account: Account, fake_api: FakeTodoApi
) -> None:
    fake_api.tasks = [_task("t1"), _task("t2")]
    sync_account(conn, work_account)
    fake_api.tasks, fake_api.expired = [_task("t2")], True

    sync_account(conn, work_account)

    assert fake_api.calls[1:] == [("list1", "https://delta/1"), ("list1", None)]
    assert _deleted_flags(conn) == {"t1": 1, "t2": 0}


def test_task_lists_are_saved_as_items(
    conn: sqlite3.Connection, work_account: Account, fake_api: FakeTodoApi
) -> None:
    sync_account(conn, work_account)

    row = conn.execute("SELECT * FROM l0_items WHERE kind = 'tasklist'").fetchone()
    assert (row["source"], row["container_id"], row["external_id"], row["title"]) == (
        "microsoft_todo",
        "",
        "list1",
        "Tasks",
    )


def test_sync_is_recorded_as_job_run(
    conn: sqlite3.Connection, work_account: Account, fake_api: FakeTodoApi
) -> None:
    fake_api.tasks = [_task("t1"), _task("t2")]

    sync_account(conn, work_account)

    row = conn.execute("SELECT * FROM lm_job_runs").fetchone()
    assert (row["job_name"], row["scope"], row["status"], row["items_processed"]) == (
        "ingest.microsoft_todo",
        "microsoft:me@work.example",
        "succeeded",
        2,
    )

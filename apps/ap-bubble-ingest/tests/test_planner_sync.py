import sqlite3
from typing import Any

import pytest

from bubble_core.accounts import Account, upsert_account
from bubble_ingest.microsoft import auth as microsoft_auth
from bubble_ingest.microsoft.planner import api
from bubble_ingest.microsoft.planner.sync import sync_account


class FakePlannerApi:
    """Serves scripted tasks and plans; a plan missing from plans cannot be read."""

    def __init__(self) -> None:
        self.tasks: list[dict[str, Any]] = []
        self.plans: dict[str, dict[str, Any]] = {"p1": {"id": "p1", "title": "Plan 1"}}

    def list_my_tasks(self, session: object) -> list[dict[str, Any]]:
        return list(self.tasks)

    def get_plan(self, session: object, plan_id: str) -> dict[str, Any] | None:
        return self.plans.get(plan_id)


@pytest.fixture
def fake_api(monkeypatch: pytest.MonkeyPatch) -> FakePlannerApi:
    fake = FakePlannerApi()
    monkeypatch.setattr(microsoft_auth, "session_for", lambda account_key: object())
    monkeypatch.setattr(api, "list_my_tasks", fake.list_my_tasks)
    monkeypatch.setattr(api, "get_plan", fake.get_plan)
    return fake


@pytest.fixture
def work_account(conn: sqlite3.Connection) -> Account:
    return upsert_account(conn, "microsoft", "me@work.example", "work")


def _task(task_id: str, plan_id: str = "p1", percent: int = 0) -> dict[str, Any]:
    return {"id": task_id, "planId": plan_id, "title": task_id, "percentComplete": percent}


def _rows(conn: sqlite3.Connection, kind: str) -> dict[str, sqlite3.Row]:
    rows = conn.execute("SELECT * FROM l0_items WHERE kind = ?", (kind,)).fetchall()
    return {row["external_id"]: row for row in rows}


def _deleted_flags(conn: sqlite3.Connection, kind: str = "task") -> dict[str, int]:
    return {eid: row["deleted"] for eid, row in _rows(conn, kind).items()}


def test_tasks_are_saved_in_their_plans(
    conn: sqlite3.Connection, work_account: Account, fake_api: FakePlannerApi
) -> None:
    fake_api.plans["p2"] = {"id": "p2", "title": "Plan 2"}
    fake_api.tasks = [_task("t1"), _task("t2", plan_id="p2", percent=100)]

    sync_account(conn, work_account)

    tasks = _rows(conn, "task")
    assert {eid: row["container_id"] for eid, row in tasks.items()} == {"t1": "p1", "t2": "p2"}
    plans = _rows(conn, "plan")
    assert {eid: row["title"] for eid, row in plans.items()} == {"p1": "Plan 1", "p2": "Plan 2"}
    assert {row["container_id"] for row in plans.values()} == {""}


def test_rerun_without_changes_changes_nothing(
    conn: sqlite3.Connection, work_account: Account, fake_api: FakePlannerApi
) -> None:
    fake_api.tasks = [_task("t1")]
    sync_account(conn, work_account)

    sync_account(conn, work_account)

    changed = conn.execute("SELECT DISTINCT changed_run_id FROM l0_items").fetchall()
    assert len(changed) == 1


def test_task_no_longer_returned_is_flagged_deleted(
    conn: sqlite3.Connection, work_account: Account, fake_api: FakePlannerApi
) -> None:
    fake_api.tasks = [_task("t1"), _task("t2")]
    sync_account(conn, work_account)
    fake_api.tasks = [_task("t2")]

    sync_account(conn, work_account)

    assert _deleted_flags(conn) == {"t1": 1, "t2": 0}


def test_plan_without_my_tasks_goes_with_its_tasks(
    conn: sqlite3.Connection, work_account: Account, fake_api: FakePlannerApi
) -> None:
    fake_api.plans["p2"] = {"id": "p2", "title": "Plan 2"}
    fake_api.tasks = [_task("t1"), _task("t2", plan_id="p2")]
    sync_account(conn, work_account)
    fake_api.tasks = [_task("t1")]

    sync_account(conn, work_account)

    assert _deleted_flags(conn) == {"t1": 0, "t2": 1}
    assert _deleted_flags(conn, "plan") == {"p1": 0, "p2": 1}


def test_unreadable_plan_is_saved_without_title(
    conn: sqlite3.Connection, work_account: Account, fake_api: FakePlannerApi
) -> None:
    fake_api.tasks = [_task("t1", plan_id="hidden")]

    sync_account(conn, work_account)

    plan = _rows(conn, "plan")["hidden"]
    assert (plan["title"], plan["deleted"]) == (None, 0)


def test_cursor_is_the_sync_time(
    conn: sqlite3.Connection, work_account: Account, fake_api: FakePlannerApi
) -> None:
    fake_api.tasks = [_task("t1")]

    sync_account(conn, work_account)

    row = conn.execute("SELECT container_id, cursor, updated_at FROM lm_sync_cursors").fetchone()
    assert row["container_id"] == "p1"
    assert row["cursor"] <= row["updated_at"]


def test_sync_is_recorded_as_job_run(
    conn: sqlite3.Connection, work_account: Account, fake_api: FakePlannerApi
) -> None:
    fake_api.tasks = [_task("t1"), _task("t2")]

    sync_account(conn, work_account)

    row = conn.execute("SELECT * FROM lm_job_runs").fetchone()
    assert (row["job_name"], row["scope"], row["status"], row["items_processed"]) == (
        "ingest.planner",
        "microsoft:me@work.example",
        "succeeded",
        2,
    )

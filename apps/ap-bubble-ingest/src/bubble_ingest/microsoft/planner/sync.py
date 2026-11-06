"""Ingest job: syncs the Planner tasks assigned to me, per plan, for every Microsoft account.

Graph v1.0 has no Planner delta, so every run is a full load: unchanged tasks are no-ops thanks to
the payload hash, and tasks no longer returned are flagged deleted. The cursor is the sync time.
A plan whose last task of mine went away is no longer listed; its tasks are flagged deleted too.
Task details (description, checklist) need a call per task and are not loaded yet.
"""

import sqlite3
from collections import defaultdict

import requests

from bubble_core.accounts import Account
from bubble_core.clock import utc_now
from bubble_core.items import Item
from bubble_core.job_log import JobRun, job_run
from bubble_core.log import get_logger
from bubble_ingest.l0_sync import ContainerChanges, apply_changes, save_containers, sync_accounts
from bubble_ingest.microsoft import auth as microsoft_auth
from bubble_ingest.microsoft.graph import Json
from bubble_ingest.microsoft.planner import api
from bubble_ingest.microsoft.planner.mapping import KIND, SOURCE, plan_to_item, to_item

JOB_NAME = f"ingest.{SOURCE}"

logger = get_logger(__name__)


def sync_all(conn: sqlite3.Connection) -> None:
    sync_accounts(conn, "microsoft", sync_account)


def sync_account(conn: sqlite3.Connection, account: Account) -> None:
    with job_run(conn, JOB_NAME, account.key) as run:
        session = microsoft_auth.session_for(account.key)
        synced_at = utc_now()
        tasks_by_plan = _tasks_by_plan(api.list_my_tasks(session))
        plans = [_plan(session, plan_id) for plan_id in tasks_by_plan]
        save_containers(conn, account, SOURCE, [plan_to_item(plan) for plan in plans], run)
        _save_tasks(conn, account, tasks_by_plan, synced_at, run)


def _save_tasks(
    conn: sqlite3.Connection,
    account: Account,
    tasks_by_plan: dict[str, list[Item]],
    synced_at: str,
    run: JobRun,
) -> None:
    """Full load per plan, including plans that only have tasks left from earlier runs."""
    plan_ids = sorted(tasks_by_plan.keys() | _plans_with_live_tasks(conn, account))
    for plan_id in plan_ids:
        changes = ContainerChanges(tasks_by_plan.get(plan_id, []), synced_at, full_load=True)
        apply_changes(conn, account, SOURCE, plan_id, changes, run)


def _tasks_by_plan(tasks: list[Json]) -> dict[str, list[Item]]:
    by_plan: dict[str, list[Item]] = defaultdict(list)
    for task in tasks:
        item = to_item(task)
        by_plan[item.container_id].append(item)
    logger.debug("%d Planner tasks in %d plans", len(tasks), len(by_plan))
    return dict(by_plan)


def _plan(session: requests.Session, plan_id: str) -> Json:
    return api.get_plan(session, plan_id) or {"id": plan_id}


def _plans_with_live_tasks(conn: sqlite3.Connection, account: Account) -> set[str]:
    rows = conn.execute(
        "SELECT DISTINCT container_id FROM l0_items "
        "WHERE account_id = ? AND source = ? AND kind = ? AND deleted = 0",
        (account.id, SOURCE, KIND),
    ).fetchall()
    logger.trace("%d plans have live tasks in L0", len(rows))
    return {row["container_id"] for row in rows}

"""Fixtures of the core tests: a job run and a quick way to put L0 rows into the vault."""

import sqlite3
from collections.abc import Callable
from typing import Any

import pytest

from bubble_core.accounts import Account
from bubble_core.items import Item, save_item
from bubble_core.job_log import job_run

type StoreItem = Callable[..., None]


@pytest.fixture
def run_id(conn: sqlite3.Connection) -> int:
    with job_run(conn, "test.job") as run:
        return run.id


@pytest.fixture
def store_item(conn: sqlite3.Connection, account: Account, run_id: int) -> StoreItem:
    """Saves an L0 item: (source, kind, container_id, external_id, payload, deleted, starts_at)."""

    def store(
        source: str,
        kind: str,
        container_id: str,
        external_id: str,
        payload: dict[str, Any],
        deleted: bool = False,
        starts_at: str | None = None,
    ) -> None:
        item = Item(
            source=source,
            container_id=container_id,
            external_id=external_id,
            kind=kind,
            title=payload.get("summary") or payload.get("title"),
            starts_at=starts_at,
            ends_at=None,
            deleted=deleted,
            payload={"id": external_id, **payload},
        )
        save_item(conn, account.id, item, run_id)
        conn.commit()

    return store

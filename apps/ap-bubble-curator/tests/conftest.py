"""Fixtures of the curator tests: L0 rows written by a finished ingest run."""

import sqlite3
from collections.abc import Callable
from typing import Any

import pytest

from bubble_core.accounts import Account
from bubble_core.items import Item, save_item
from bubble_core.job_log import job_run

type Store = Callable[..., int]


@pytest.fixture
def store(conn: sqlite3.Connection, account: Account) -> Store:
    """store(source, kind, external_id, payload, ...) -> l0 item id, saved by a finished run."""

    def store(
        source: str,
        kind: str,
        external_id: str,
        payload: dict[str, Any],
        *,
        container_id: str = "c",
        title: str | None = None,
        starts_at: str | None = None,
        ends_at: str | None = None,
        deleted: bool = False,
    ) -> int:
        item = Item(
            source, container_id, external_id, kind, title, starts_at, ends_at, deleted, payload
        )
        with job_run(conn, f"ingest.{source}", account.key) as run:
            save_item(conn, account.id, item, run.id)
        row = conn.execute(
            "SELECT id FROM l0_items WHERE external_id = ?", (external_id,)
        ).fetchone()
        return row["id"]

    return store

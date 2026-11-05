"""L0 items (l0_items): everything ingested from external systems. Callers commit."""

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from bubble_core.clock import utc_now
from bubble_core.log import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class Item:
    """One item as a source delivered it: common fields for queries, everything in payload."""

    source: str  # e.g. 'google_calendar'
    container_id: str  # e.g. calendar id; '' when the source has none
    external_id: str
    kind: str  # 'event', 'mail', 'task', 'contact', ...
    title: str | None
    starts_at: str | None
    ends_at: str | None
    deleted: bool
    payload: dict[str, Any]


def save_item(conn: sqlite3.Connection, account_id: int, item: Item, run_id: int) -> bool:
    """Insert or update the item; return True when it is new or really changed.

    A deletion only flags a known row, so what was known about the item is kept.
    """
    payload, payload_hash = _serialize(item.payload)
    row = _find(conn, account_id, item)
    if row is None:
        _insert(conn, account_id, item, payload, payload_hash, run_id)
    elif item.deleted:
        if row["deleted"]:
            return False
        _flag_deleted(conn, [row["id"]], run_id)
    elif row["payload_hash"] != payload_hash or row["deleted"]:
        _update(conn, row["id"], item, payload, payload_hash, run_id)
    else:
        return False
    logger.trace("Saved %s %s (deleted=%s)", item.kind, item.external_id, item.deleted)
    return True


def flag_missing_deleted(
    conn: sqlite3.Connection,
    account_id: int,
    source: str,
    container_id: str,
    seen_ids: set[str],
    run_id: int,
) -> int:
    """After a full load: flag container items the source no longer returned as deleted."""
    rows = conn.execute(
        "SELECT id, external_id FROM l0_items "
        "WHERE account_id = ? AND source = ? AND container_id = ? AND deleted = 0",
        (account_id, source, container_id),
    ).fetchall()
    missing = [row["id"] for row in rows if row["external_id"] not in seen_ids]
    _flag_deleted(conn, missing, run_id)
    logger.debug("Flagged %d missing %s items as deleted", len(missing), source)
    return len(missing)


def _serialize(payload: dict[str, Any]) -> tuple[str, str]:
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest()


def _find(conn: sqlite3.Connection, account_id: int, item: Item) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, payload_hash, deleted FROM l0_items "
        "WHERE account_id = ? AND source = ? AND container_id = ? AND external_id = ?",
        (account_id, item.source, item.container_id, item.external_id),
    ).fetchone()


def _insert(
    conn: sqlite3.Connection,
    account_id: int,
    item: Item,
    payload: str,
    payload_hash: str,
    run_id: int,
) -> None:
    conn.execute(
        "INSERT INTO l0_items (account_id, source, container_id, external_id, kind, title, "
        "starts_at, ends_at, deleted, payload, payload_hash, changed_run_id, created_at, "
        "changed_at) VALUES (:account_id, :source, :container_id, :external_id, :kind, :title, "
        ":starts_at, :ends_at, :deleted, :payload, :payload_hash, :run_id, :now, :now)",
        _params(item, payload, payload_hash, run_id) | {"account_id": account_id},
    )


def _update(
    conn: sqlite3.Connection, row_id: int, item: Item, payload: str, payload_hash: str, run_id: int
) -> None:
    conn.execute(
        "UPDATE l0_items SET kind = :kind, title = :title, starts_at = :starts_at, "
        "ends_at = :ends_at, deleted = :deleted, payload = :payload, "
        "payload_hash = :payload_hash, changed_run_id = :run_id, changed_at = :now "
        "WHERE id = :id",
        _params(item, payload, payload_hash, run_id) | {"id": row_id},
    )


def _flag_deleted(conn: sqlite3.Connection, row_ids: list[int], run_id: int) -> None:
    now = utc_now()
    conn.executemany(
        "UPDATE l0_items SET deleted = 1, changed_run_id = ?, changed_at = ? WHERE id = ?",
        [(run_id, now, row_id) for row_id in row_ids],
    )


def _params(item: Item, payload: str, payload_hash: str, run_id: int) -> dict[str, Any]:
    return {
        "source": item.source,
        "container_id": item.container_id,
        "external_id": item.external_id,
        "kind": item.kind,
        "title": item.title,
        "starts_at": item.starts_at,
        "ends_at": item.ends_at,
        "deleted": int(item.deleted),
        "payload": payload,
        "payload_hash": payload_hash,
        "run_id": run_id,
        "now": utc_now(),
    }

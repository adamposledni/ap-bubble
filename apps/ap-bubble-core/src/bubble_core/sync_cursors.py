"""Sync cursors (lm_sync_cursors): where each incremental sync left off. Callers commit."""

import sqlite3

from bubble_core.clock import utc_now
from bubble_core.log import get_logger

logger = get_logger(__name__)


def load_cursor(
    conn: sqlite3.Connection, account_id: int, source: str, container_id: str
) -> str | None:
    row = conn.execute(
        "SELECT cursor FROM lm_sync_cursors "
        "WHERE account_id = ? AND source = ? AND container_id = ?",
        (account_id, source, container_id),
    ).fetchone()
    logger.trace("Cursor of %s/%s for account %d: %s", source, container_id, account_id, bool(row))
    return row["cursor"] if row else None


def save_cursor(
    conn: sqlite3.Connection, account_id: int, source: str, container_id: str, cursor: str
) -> None:
    conn.execute(
        "INSERT INTO lm_sync_cursors (account_id, source, container_id, cursor, updated_at) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT (account_id, source, container_id) "
        "DO UPDATE SET cursor = excluded.cursor, updated_at = excluded.updated_at",
        (account_id, source, container_id, cursor, utc_now()),
    )
    logger.trace("Saved cursor of %s/%s for account %d", source, container_id, account_id)

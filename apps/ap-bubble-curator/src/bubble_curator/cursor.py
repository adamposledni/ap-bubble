"""The curator's place in the L0 change set (lm_curator_cursor), in (changed_run_id, id) order."""

import sqlite3
from dataclasses import dataclass

from bubble_core.clock import utc_now
from bubble_core.log import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, order=True)
class Position:
    changed_run_id: int
    item_id: int


START = Position(0, 0)


def load_position(conn: sqlite3.Connection) -> Position:
    row = conn.execute("SELECT changed_run_id, item_id FROM lm_curator_cursor").fetchone()
    position = Position(row["changed_run_id"], row["item_id"]) if row else START
    logger.debug("Curator cursor at %s", position)
    return position


def save_position(conn: sqlite3.Connection, position: Position) -> None:
    """Commits."""
    conn.execute(
        "INSERT INTO lm_curator_cursor (id, changed_run_id, item_id, updated_at) "
        "VALUES (1, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET "
        "changed_run_id = excluded.changed_run_id, item_id = excluded.item_id, "
        "updated_at = excluded.updated_at",
        (position.changed_run_id, position.item_id, utc_now()),
    )
    conn.commit()
    logger.debug("Curator cursor moved to %s", position)

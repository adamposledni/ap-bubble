"""Applies numbered SQL migrations (migrations/NNNN_name.sql), tracked by PRAGMA user_version."""

import sqlite3
from contextlib import closing
from importlib.resources import files
from pathlib import Path
from typing import NamedTuple

from ap_adams_bubble_core.db.connection import connect
from ap_adams_bubble_core.log import get_logger

logger = get_logger(__name__)


class Migration(NamedTuple):
    version: int
    name: str
    sql: str


def migrate(path: Path | None = None) -> int:
    """Apply pending migrations in one transaction and return the schema version.

    The write lock is taken before the version is read, so processes starting at once are safe.
    """
    with closing(connect(path, autocommit=True)) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            version = _apply_pending(conn)
            conn.execute("COMMIT")
        except BaseException:
            if conn.in_transaction:  # some SQLite errors already rolled back
                conn.execute("ROLLBACK")
            raise
    return version


def _apply_pending(conn: sqlite3.Connection) -> int:
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    pending = [m for m in _load_migrations() if m.version > current]
    if not pending:
        logger.debug("Schema is up to date at version %d", current)
        return current

    for migration in pending:
        logger.info("Applying migration %s", migration.name)
        conn.executescript(migration.sql)
    latest = pending[-1].version
    conn.execute(f"PRAGMA user_version = {latest}")
    return latest


def _load_migrations() -> list[Migration]:
    folder = files("ap_adams_bubble_core.db") / "migrations"
    migrations = [
        Migration(int(f.name.split("_", 1)[0]), f.name, f.read_text(encoding="utf-8"))
        for f in folder.iterdir()
        if f.name.endswith(".sql")
    ]
    return sorted(migrations)

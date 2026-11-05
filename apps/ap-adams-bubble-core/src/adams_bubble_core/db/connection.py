"""SQLite connections to the vault database."""

import sqlite3
from pathlib import Path

from adams_bubble_core.log import get_logger
from adams_bubble_core.paths import db_path

_BUSY_TIMEOUT_SECONDS = 5.0

logger = get_logger(__name__)


def connect(
    path: Path | None = None,
    autocommit: bool | int = sqlite3.LEGACY_TRANSACTION_CONTROL,
) -> sqlite3.Connection:
    """Open the vault DB with WAL (several processes share it) and foreign keys enforced."""
    target = path or db_path()
    logger.trace("Opening database %s", target)
    conn = sqlite3.connect(target, timeout=_BUSY_TIMEOUT_SECONDS, autocommit=autocommit)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

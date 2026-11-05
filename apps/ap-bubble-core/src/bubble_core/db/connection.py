"""SQLite connections to the vault database."""

import sqlite3
from pathlib import Path

from bubble_core.log import get_logger
from bubble_core.paths import db_path

_BUSY_TIMEOUT_SECONDS = 5.0

logger = get_logger(__name__)


def connect(
    path: Path | None = None,
    autocommit: bool | int = sqlite3.LEGACY_TRANSACTION_CONTROL,
    check_same_thread: bool = True,
) -> sqlite3.Connection:
    """Open the vault DB with WAL (several processes share it) and foreign keys enforced.

    check_same_thread=False lets one request's worker threads share a connection in turn.
    """
    target = path or db_path()
    logger.trace("Opening database %s", target)
    conn = sqlite3.connect(
        target,
        timeout=_BUSY_TIMEOUT_SECONDS,
        autocommit=autocommit,
        check_same_thread=check_same_thread,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

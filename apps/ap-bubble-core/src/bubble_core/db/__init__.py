"""Vault database: connections and schema migrations."""

import sqlite3
from pathlib import Path

from bubble_core.db.connection import connect
from bubble_core.db.migrate import migrate

__all__ = ["connect", "migrate", "open_vault"]


def open_vault(path: Path | None = None) -> sqlite3.Connection:
    """Bring the schema up to date and return a connection to the vault DB."""
    migrate(path)
    return connect(path)

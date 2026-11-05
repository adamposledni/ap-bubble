"""Test fixtures shared by all components."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest

from bubble_core.accounts import Account, upsert_account
from bubble_core.db import open_vault


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "vault.db"


@pytest.fixture
def conn(vault_path: Path) -> Iterator[sqlite3.Connection]:
    with closing(open_vault(vault_path)) as conn:
        yield conn


@pytest.fixture
def account(conn: sqlite3.Connection) -> Account:
    return upsert_account(conn, "google", "me@gmail.com", "personal")

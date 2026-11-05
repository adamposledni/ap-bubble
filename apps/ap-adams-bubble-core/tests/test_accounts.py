import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest

from adams_bubble_core.accounts import list_accounts, upsert_account
from adams_bubble_core.db import open_vault


@pytest.fixture
def conn(vault_path: Path) -> Iterator[sqlite3.Connection]:
    with closing(open_vault(vault_path)) as conn:
        yield conn


def test_upsert_adds_account_with_lower_case_email(conn: sqlite3.Connection) -> None:
    account = upsert_account(conn, "google", "Me@Gmail.com", "personal")

    assert account.key == "google:me@gmail.com"
    assert list_accounts(conn) == [account]


def test_upsert_of_known_account_updates_context(conn: sqlite3.Connection) -> None:
    first = upsert_account(conn, "google", "me@gmail.com", "personal")
    second = upsert_account(conn, "google", "me@gmail.com", "work")

    assert second.id == first.id
    assert second.context == "work"


def test_list_accounts_filters_by_provider(conn: sqlite3.Connection) -> None:
    google = upsert_account(conn, "google", "me@gmail.com", "personal")
    upsert_account(conn, "microsoft", "me@work.com", "work")

    assert list_accounts(conn, "google") == [google]

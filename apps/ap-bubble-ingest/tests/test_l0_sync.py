import sqlite3

import pytest

from bubble_core.accounts import Account, upsert_account
from bubble_ingest.l0_sync import sync_accounts


def test_failed_account_does_not_stop_the_others(conn: sqlite3.Connection) -> None:
    upsert_account(conn, "google", "broken@gmail.com", "personal")
    upsert_account(conn, "google", "fine@gmail.com", "personal")
    synced: list[str] = []

    def sync_account(conn: sqlite3.Connection, account: Account) -> None:
        if account.email == "broken@gmail.com":
            raise RuntimeError("boom")
        synced.append(account.email)

    with pytest.raises(RuntimeError, match="broken@gmail.com"):
        sync_accounts(conn, "google", sync_account)
    assert synced == ["fine@gmail.com"]

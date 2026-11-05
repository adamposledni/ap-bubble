import sqlite3

from bubble_core.accounts import Account
from bubble_core.sync_cursors import load_cursor, save_cursor


def test_cursor_is_none_until_saved(conn: sqlite3.Connection, account: Account) -> None:
    assert load_cursor(conn, account.id, "test", "c1") is None


def test_saved_cursor_is_loaded_and_replaced(conn: sqlite3.Connection, account: Account) -> None:
    save_cursor(conn, account.id, "test", "c1", "t1")
    save_cursor(conn, account.id, "test", "c1", "t2")

    assert load_cursor(conn, account.id, "test", "c1") == "t2"

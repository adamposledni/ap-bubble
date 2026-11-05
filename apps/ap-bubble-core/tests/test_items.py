import sqlite3
from typing import Any

from bubble_core.accounts import Account
from bubble_core.items import Item, flag_deleted, flag_missing_deleted, save_item


def _item(external_id: str = "e1", deleted: bool = False, **payload: Any) -> Item:
    return Item(
        source="test",
        container_id="c1",
        external_id=external_id,
        kind="event",
        title=payload.get("summary"),
        starts_at=None,
        ends_at=None,
        deleted=deleted,
        payload={"id": external_id, **payload},
    )


def _row(conn: sqlite3.Connection, external_id: str = "e1") -> sqlite3.Row:
    return conn.execute("SELECT * FROM l0_items WHERE external_id = ?", (external_id,)).fetchone()


def test_new_item_is_saved(conn: sqlite3.Connection, account: Account, run_id: int) -> None:
    assert save_item(conn, account.id, _item(summary="Lunch"), run_id)
    assert _row(conn)["title"] == "Lunch"


def test_unchanged_item_is_no_change(
    conn: sqlite3.Connection, account: Account, run_id: int
) -> None:
    save_item(conn, account.id, _item(summary="Lunch"), run_id)

    assert not save_item(conn, account.id, _item(summary="Lunch"), run_id)


def test_changed_item_is_updated(conn: sqlite3.Connection, account: Account, run_id: int) -> None:
    save_item(conn, account.id, _item(summary="Lunch"), run_id)

    assert save_item(conn, account.id, _item(summary="Dinner"), run_id)
    assert _row(conn)["title"] == "Dinner"


def test_deletion_flags_row_and_keeps_known_content(
    conn: sqlite3.Connection, account: Account, run_id: int
) -> None:
    save_item(conn, account.id, _item(summary="Lunch"), run_id)

    assert save_item(conn, account.id, _item(deleted=True, status="cancelled"), run_id)
    assert not save_item(conn, account.id, _item(deleted=True, status="cancelled"), run_id)
    row = _row(conn)
    assert (row["deleted"], row["title"]) == (1, "Lunch")


def test_deletion_of_unknown_item_is_stored(
    conn: sqlite3.Connection, account: Account, run_id: int
) -> None:
    assert save_item(conn, account.id, _item(deleted=True, status="cancelled"), run_id)
    assert _row(conn)["deleted"] == 1


def test_restored_item_is_undeleted(
    conn: sqlite3.Connection, account: Account, run_id: int
) -> None:
    save_item(conn, account.id, _item(summary="Lunch"), run_id)
    save_item(conn, account.id, _item(deleted=True), run_id)

    assert save_item(conn, account.id, _item(summary="Lunch"), run_id)
    assert _row(conn)["deleted"] == 0


def test_flag_missing_deleted_flags_only_unseen_items(
    conn: sqlite3.Connection, account: Account, run_id: int
) -> None:
    save_item(conn, account.id, _item("e1"), run_id)
    save_item(conn, account.id, _item("e2"), run_id)

    assert flag_missing_deleted(conn, account.id, "test", "c1", {"e1"}, run_id) == 1
    assert (_row(conn, "e1")["deleted"], _row(conn, "e2")["deleted"]) == (0, 1)


def test_flag_deleted_flags_known_items_and_skips_unknown_ones(
    conn: sqlite3.Connection, account: Account, run_id: int
) -> None:
    save_item(conn, account.id, _item("e1", summary="Lunch"), run_id)
    save_item(conn, account.id, _item("e2"), run_id)

    assert flag_deleted(conn, account.id, "test", "c1", ["e1", "unknown"], run_id) == 1
    assert flag_deleted(conn, account.id, "test", "c1", ["e1"], run_id) == 0
    assert (_row(conn, "e1")["deleted"], _row(conn, "e1")["title"]) == (1, "Lunch")
    assert _row(conn, "e2")["deleted"] == 0
    assert _row(conn, "unknown") is None

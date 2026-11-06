import sqlite3
from collections.abc import Callable

from bubble_core.job_log import _start
from bubble_curator.changes import read_changes
from bubble_curator.cursor import START, Position

type Store = Callable[..., int]


def _mail(store: Store, external_id: str) -> int:
    return store("gmail", "mail", external_id, {}, starts_at="2026-11-01T10:00:00+00:00")


def test_rows_come_in_cursor_order_after_the_position(
    conn: sqlite3.Connection, store: Store
) -> None:
    first, second = _mail(store, "a"), _mail(store, "b")

    everything = read_changes(conn, START, lambda item: True, max_kept=10)
    after_first = read_changes(conn, _position(conn, first), lambda item: True, max_kept=10)

    assert [i.id for i in everything.items] == [first, second]
    assert [i.id for i in after_first.items] == [second]


def test_skipped_rows_still_move_the_end(conn: sqlite3.Connection, store: Store) -> None:
    _mail(store, "a")
    last = _mail(store, "b")

    changes = read_changes(conn, START, lambda item: False, max_kept=10)

    assert changes.items == [] and changes.end == _position(conn, last)


def test_rows_of_a_running_ingest_run_wait(conn: sqlite3.Connection, store: Store) -> None:
    done = _mail(store, "a")
    _start(conn, "ingest.gmail", None)  # a run that has not finished
    _mail(store, "b")

    changes = read_changes(conn, START, lambda item: True, max_kept=10)

    assert [i.id for i in changes.items] == [done]


def _position(conn: sqlite3.Connection, item_id: int) -> Position:
    row = conn.execute("SELECT changed_run_id FROM l0_items WHERE id = ?", (item_id,)).fetchone()
    return Position(row["changed_run_id"], item_id)

import sqlite3

from bubble_core.input_queue import queued_inputs, requeue_failed, requeue_stuck, set_status
from bubble_core.inputs import add_input, get_input


def test_queued_inputs_come_oldest_first(conn: sqlite3.Connection) -> None:
    first = add_input(conn, "first", [])
    second = add_input(conn, "second", [])
    set_status(conn, [first.id], "done")

    assert [i.id for i in queued_inputs(conn, 10)] == [second.id]


def test_done_and_failed_record_when_and_why(conn: sqlite3.Connection) -> None:
    item = add_input(conn, "note", [])

    set_status(conn, [item.id], "processing")
    assert get_input(conn, item.id).processed_at is None

    set_status(conn, [item.id], "failed", "claude exited with 1")
    failed = get_input(conn, item.id)
    assert (failed.status, failed.error) == ("failed", "claude exited with 1")
    assert failed.processed_at is not None


def test_stuck_inputs_go_back_to_the_queue(conn: sqlite3.Connection) -> None:
    item = add_input(conn, "note", [])
    set_status(conn, [item.id], "processing")

    assert requeue_stuck(conn) == 1
    assert get_input(conn, item.id).status == "queued"


def test_failed_inputs_are_retried_until_attempts_run_out(conn: sqlite3.Connection) -> None:
    item = add_input(conn, "note", [])

    set_status(conn, [item.id], "failed", "boom")
    assert requeue_failed(conn, max_attempts=2) == 1
    set_status(conn, [item.id], "failed", "boom")

    assert requeue_failed(conn, max_attempts=2) == 0
    assert get_input(conn, item.id).status == "failed"

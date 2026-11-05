import io
import sqlite3

import pytest

from bubble_core.inbox import safe_name
from bubble_core.inputs import (
    InputNotFound,
    InputNotQueued,
    NewFile,
    add_input,
    delete_input,
    get_file,
    list_inputs,
)


def _file(name: str = "note.txt", content: bytes = b"hello") -> NewFile:
    return NewFile(name=name, media_type="text/plain", content=io.BytesIO(content))


def test_text_input_is_queued(conn: sqlite3.Connection) -> None:
    added = add_input(conn, "  Petr's birthday is 3 May  ", [])

    assert (added.text, added.status, added.files) == ("Petr's birthday is 3 May", "queued", [])
    assert list_inputs(conn) == [added]


def test_files_are_stored_in_the_inbox(conn: sqlite3.Connection) -> None:
    added = add_input(conn, None, [_file("a.txt", b"one"), _file("b.txt", b"two")])

    assert [f.name for f in added.files] == ["a.txt", "b.txt"]
    file, path = get_file(conn, added.files[1].id)
    assert (file.size_bytes, path.read_bytes()) == (3, b"two")


def test_empty_input_is_rejected(conn: sqlite3.Connection) -> None:
    with pytest.raises(ValueError):
        add_input(conn, "   ", [])


def test_inputs_are_listed_newest_first(conn: sqlite3.Connection) -> None:
    first = add_input(conn, "first", [])
    second = add_input(conn, "second", [])

    assert [i.id for i in list_inputs(conn)] == [second.id, first.id]


def test_queued_input_is_deleted_with_its_files(conn: sqlite3.Connection) -> None:
    added = add_input(conn, "note", [_file()])
    _, path = get_file(conn, added.files[0].id)

    delete_input(conn, added.id)

    assert list_inputs(conn) == []
    assert not path.exists()
    with pytest.raises(InputNotFound):
        get_file(conn, added.files[0].id)


def test_input_taken_by_the_curator_cannot_be_deleted(conn: sqlite3.Connection) -> None:
    added = add_input(conn, "note", [])
    conn.execute("UPDATE l1_inputs SET status = 'processing' WHERE id = ?", (added.id,))
    conn.commit()

    with pytest.raises(InputNotQueued):
        delete_input(conn, added.id)


def test_safe_name_drops_folders_and_forbidden_characters() -> None:
    assert safe_name("..\\..\\evil:name?.txt") == "evil_name_.txt"
    assert safe_name("...") == "file"

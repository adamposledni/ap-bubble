"""L1 input queue (l1_inputs, l1_input_files): my own text and files, waiting for the curator."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Literal, cast

from bubble_core import inbox
from bubble_core.clock import utc_now
from bubble_core.log import get_logger

Status = Literal["queued", "processing", "done", "failed"]

logger = get_logger(__name__)


class InputNotFound(LookupError):
    pass


class InputNotQueued(Exception):
    """The curator has already taken the input, so it can no longer be changed."""


@dataclass(frozen=True)
class NewFile:
    name: str
    media_type: str | None
    content: BinaryIO


@dataclass(frozen=True)
class InputFile:
    id: int
    name: str
    media_type: str | None
    size_bytes: int
    stored_path: str  # relative to the inbox folder


@dataclass(frozen=True)
class Input:
    id: int
    text: str | None
    status: Status
    error: str | None
    created_at: str
    processed_at: str | None
    files: list[InputFile]


def add_input(conn: sqlite3.Connection, text: str | None, files: list[NewFile]) -> Input:
    """Queue text and/or files as one input."""
    text = (text or "").strip() or None
    if text is None and not files:
        raise ValueError("An input needs text or at least one file")
    cursor = conn.execute(
        "INSERT INTO l1_inputs (text, created_at) VALUES (?, ?)", (text, utc_now())
    )
    input_id = cursor.lastrowid or 0
    try:
        for index, file in enumerate(files, start=1):
            _add_file(conn, input_id, index, file)
        conn.commit()
    except BaseException:
        conn.rollback()
        inbox.remove_files(input_id)
        raise
    logger.info("Queued input %d (text: %s, files: %d)", input_id, text is not None, len(files))
    return get_input(conn, input_id)


def list_inputs(
    conn: sqlite3.Connection, limit: int = 100, include_done: bool = True
) -> list[Input]:
    """The newest inputs first; done ones only if asked for."""
    where = "" if include_done else "WHERE status != 'done'"
    rows = conn.execute(
        f"SELECT * FROM l1_inputs {where} ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    files = _files_of(conn, [row["id"] for row in rows])
    return [_to_input(row, files.get(row["id"], [])) for row in rows]


def get_input(conn: sqlite3.Connection, input_id: int) -> Input:
    row = conn.execute("SELECT * FROM l1_inputs WHERE id = ?", (input_id,)).fetchone()
    if row is None:
        raise InputNotFound(f"Input {input_id} not found")
    return _to_input(row, _files_of(conn, [input_id]).get(input_id, []))


def get_file(conn: sqlite3.Connection, file_id: int) -> tuple[InputFile, Path]:
    """The file's record and where it is stored."""
    row = conn.execute("SELECT * FROM l1_input_files WHERE id = ?", (file_id,)).fetchone()
    if row is None:
        raise InputNotFound(f"Input file {file_id} not found")
    file = _to_file(row)
    return file, inbox.path_of(file.stored_path)


def delete_input(conn: sqlite3.Connection, input_id: int) -> None:
    """Delete a still-queued input with its files."""
    if get_input(conn, input_id).status != "queued":
        raise InputNotQueued(f"Input {input_id} is no longer queued")
    conn.execute("DELETE FROM l1_inputs WHERE id = ?", (input_id,))
    conn.commit()
    inbox.remove_files(input_id)
    logger.info("Deleted input %d", input_id)


def _add_file(conn: sqlite3.Connection, input_id: int, index: int, file: NewFile) -> None:
    stored_path, size = inbox.store_file(input_id, index, file.name, file.content)
    conn.execute(
        "INSERT INTO l1_input_files (input_id, file_name, stored_path, media_type, size_bytes) "
        "VALUES (?, ?, ?, ?, ?)",
        (input_id, file.name, stored_path, file.media_type, size),
    )


def _files_of(conn: sqlite3.Connection, input_ids: list[int]) -> dict[int, list[InputFile]]:
    marks = ",".join("?" * len(input_ids))
    rows = conn.execute(
        f"SELECT * FROM l1_input_files WHERE input_id IN ({marks}) ORDER BY id", input_ids
    ).fetchall()
    files: dict[int, list[InputFile]] = {}
    for row in rows:
        files.setdefault(row["input_id"], []).append(_to_file(row))
    return files


def _to_file(row: sqlite3.Row) -> InputFile:
    return InputFile(
        id=row["id"],
        name=row["file_name"],
        media_type=row["media_type"],
        size_bytes=row["size_bytes"],
        stored_path=row["stored_path"],
    )


def _to_input(row: sqlite3.Row, files: list[InputFile]) -> Input:
    return Input(
        id=row["id"],
        text=row["text"],
        status=cast(Status, row["status"]),
        error=row["error"],
        created_at=row["created_at"],
        processed_at=row["processed_at"],
        files=files,
    )

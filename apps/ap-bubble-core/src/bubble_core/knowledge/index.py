"""The SQLite full-text index of the knowledge files (l2_knowledge_files, l2_knowledge_fts).

The files stay the truth: sync_index only stats them and re-reads the new or changed ones,
so keeping the index current costs one stat per file when nothing changed.
"""

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from bubble_core.knowledge.files import file_paths, load_file
from bubble_core.knowledge.fold import fold
from bubble_core.knowledge.model import Folder, KnowledgeFile
from bubble_core.knowledge.plain import plain_text
from bubble_core.log import get_logger

logger = get_logger(__name__)

_UPSERT_FILE = """
    INSERT INTO l2_knowledge_files
        (ref, folder, slug, name, name_key, tags, updated, plain, mtime_ns, size_bytes)
    VALUES (:ref, :folder, :slug, :name, :name_key, :tags, :updated, :plain, :mtime_ns, :size)
    ON CONFLICT (ref) DO UPDATE SET
        name = excluded.name, name_key = excluded.name_key, tags = excluded.tags,
        updated = excluded.updated, plain = excluded.plain,
        mtime_ns = excluded.mtime_ns, size_bytes = excluded.size_bytes
    RETURNING id
"""
_INSERT_FTS = "INSERT INTO l2_knowledge_fts (rowid, names, details, body) VALUES (?, ?, ?, ?)"


@dataclass(frozen=True)
class _Stat:
    folder: Folder
    path: Path
    mtime_ns: int
    size: int

    @property
    def ref(self) -> str:
        return f"{self.folder}/{self.path.stem}"


@dataclass(frozen=True)
class _Indexed:
    id: int
    mtime_ns: int
    size: int


def sync_index(conn: sqlite3.Connection) -> None:
    """Bring the index in line with the files: (re)index new and changed, drop vanished ones."""
    on_disk = _stat_files()
    indexed = _indexed(conn)
    changed = [stat for ref, stat in on_disk.items() if _is_changed(stat, indexed.get(ref))]
    vanished = [entry.id for ref, entry in indexed.items() if ref not in on_disk]
    if not changed and not vanished:
        logger.trace("Knowledge index is current (%d files)", len(on_disk))
        return
    with conn:  # one transaction, committed or rolled back
        indexed_count = sum(_index_file(conn, stat) for stat in changed)
        for file_id in vanished:
            _remove(conn, file_id)
    logger.debug(
        "Synced knowledge index: %d (re)indexed, %d removed, %d files",
        indexed_count,
        len(vanished),
        len(on_disk),
    )


def _stat_files() -> dict[str, _Stat]:
    stats = (_stat(folder, path) for folder, path in file_paths())
    return {stat.ref: stat for stat in stats if stat is not None}


def _stat(folder: Folder, path: Path) -> _Stat | None:
    try:
        info = path.stat()
    except FileNotFoundError:  # deleted since it was listed
        logger.trace("Knowledge file vanished while syncing: %s", path)
        return None
    return _Stat(folder=folder, path=path, mtime_ns=info.st_mtime_ns, size=info.st_size)


def _indexed(conn: sqlite3.Connection) -> dict[str, _Indexed]:
    rows = conn.execute("SELECT id, ref, mtime_ns, size_bytes FROM l2_knowledge_files")
    return {row["ref"]: _Indexed(row["id"], row["mtime_ns"], row["size_bytes"]) for row in rows}


def _is_changed(stat: _Stat, entry: _Indexed | None) -> bool:
    return entry is None or (entry.mtime_ns, entry.size) != (stat.mtime_ns, stat.size)


def _index_file(conn: sqlite3.Connection, stat: _Stat) -> bool:
    """Upsert the file's row and replace its full-text row; False when it cannot be read."""
    try:
        file = load_file(stat.folder, stat.path)
    except OSError as error:  # deleted or locked since the stat; the next sync retries
        logger.warning("Cannot index knowledge file %s: %s", stat.path, error)
        return False
    plain = plain_text(file.body)
    file_id = conn.execute(_UPSERT_FILE, _file_row(file, plain, stat)).fetchone()["id"]
    conn.execute("DELETE FROM l2_knowledge_fts WHERE rowid = ?", (file_id,))
    conn.execute(_INSERT_FTS, (file_id, *_fts_columns(file, plain)))
    logger.trace("Indexed knowledge file %s as %d", file.ref, file_id)
    return True


def _file_row(file: KnowledgeFile, plain: str, stat: _Stat) -> dict[str, object]:
    return {
        "ref": file.ref,
        "folder": file.folder,
        "slug": file.slug,
        "name": file.meta.name,
        "name_key": fold(file.meta.name),
        "tags": json.dumps(file.meta.tags, ensure_ascii=False),
        "updated": file.meta.updated,
        "plain": plain,
        "mtime_ns": stat.mtime_ns,
        "size": stat.size,
    }


def _fts_columns(file: KnowledgeFile, plain: str) -> tuple[str, str, str]:
    """(names, details, body), folded like the query words."""
    meta = file.meta
    names = " ".join([meta.name, *meta.aliases, file.slug])
    details = " ".join([*meta.tags, *meta.emails, *meta.phones])
    return fold(names), fold(details), fold(plain)


def _remove(conn: sqlite3.Connection, file_id: int) -> None:
    conn.execute("DELETE FROM l2_knowledge_fts WHERE rowid = ?", (file_id,))
    conn.execute("DELETE FROM l2_knowledge_files WHERE id = ?", (file_id,))
    logger.trace("Removed knowledge file %d from the index", file_id)

import sqlite3
from collections.abc import Callable
from pathlib import Path

import pytest

from bubble_core.inputs import add_input, get_input
from bubble_curator import run as run_module
from bubble_curator.claude import CurationFailed
from bubble_curator.cursor import START, load_position
from bubble_curator.run import Options, run

type Store = Callable[..., int]

RECENT = "2026-11-01T10:00:00+00:00"


class FakeClaude:
    """Stands in for curate_batch: records batch files, fails when told to."""

    def __init__(self) -> None:
        self.batches: list[Path] = []
        self.fail = False

    def __call__(self, batch_file: Path, index_file: Path) -> str:
        assert index_file.exists()  # written before every batch
        self.batches.append(batch_file)
        if self.fail:
            raise CurationFailed("claude exited with 1")
        return "updated people/petr.md"


@pytest.fixture
def claude(monkeypatch: pytest.MonkeyPatch) -> FakeClaude:
    fake = FakeClaude()
    monkeypatch.setattr(run_module, "curate_batch", fake)
    monkeypatch.setattr(run_module, "window_start", lambda days: "2026-10-01T00:00:00+00:00")
    return fake


def _mail(store: Store, external_id: str) -> int:
    payload = {"threadId": external_id, "snippet": "Contract signed"}
    return store("gmail", "mail", external_id, payload, title="Contract", starts_at=RECENT)


def _status(conn: sqlite3.Connection, input_id: int) -> str:
    return get_input(conn, input_id).status


def test_inputs_and_changes_are_curated_and_the_cursor_moves(
    conn: sqlite3.Connection, store: Store, claude: FakeClaude
) -> None:
    note = add_input(conn, "Petr's birthday is 3 May", [])
    _mail(store, "m1")

    run(conn, Options())

    assert len(claude.batches) == 1
    text = claude.batches[0].read_text(encoding="utf-8")
    assert "Petr's birthday" in text and "Contract signed" in text
    assert _status(conn, note.id) == "done"
    assert load_position(conn) != START


def test_failed_batch_fails_its_inputs_and_keeps_the_cursor(
    conn: sqlite3.Connection, store: Store, claude: FakeClaude
) -> None:
    note = add_input(conn, "note", [])
    _mail(store, "m1")
    claude.fail = True

    with pytest.raises(CurationFailed):
        run(conn, Options())

    assert get_input(conn, note.id).error == "claude exited with 1"
    assert _status(conn, note.id) == "failed"
    assert load_position(conn) == START


def test_dry_run_only_writes_batch_files(
    conn: sqlite3.Connection, store: Store, claude: FakeClaude
) -> None:
    note = add_input(conn, "note", [])
    _mail(store, "m1")

    run(conn, Options(dry_run=True))

    assert claude.batches == []
    assert _status(conn, note.id) == "queued"
    assert load_position(conn) == START
    run_row = conn.execute("SELECT * FROM lm_job_runs WHERE job_name LIKE 'curator.%'").fetchone()
    assert run_row["job_name"] == "curator.dry_run"


def test_nothing_new_exits_early_but_moves_past_noise(
    conn: sqlite3.Connection, store: Store, claude: FakeClaude
) -> None:
    store("gmail", "mail", "promo", {"labelIds": ["CATEGORY_PROMOTIONS"]}, starts_at=RECENT)

    run(conn, Options())

    assert claude.batches == []
    assert load_position(conn) != START

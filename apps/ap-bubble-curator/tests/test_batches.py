from pathlib import Path

from bubble_curator.batches import pack, write_batches
from bubble_curator.settings import FILE_CHARS
from bubble_curator.unit import Unit


def _unit(n: int, size: int) -> Unit:
    return Unit(f"unit {n}", "x" * size, sort_key=str(n), item_ids=[n])


def test_units_are_packed_until_a_batch_is_full() -> None:
    batches = pack([_unit(1, 400), _unit(2, 400), _unit(3, 400)], max_chars=1000)

    assert [[u.item_ids[0] for u in b.units] for b in batches] == [[1, 2], [3]]


def test_a_unit_too_big_for_any_batch_is_cut() -> None:
    [batch] = pack([_unit(1, 5000)], max_chars=1000)

    assert batch.weight <= 1000


def test_attached_files_weigh_in_so_an_input_with_many_files_gets_its_own_batch() -> None:
    with_files = Unit("input", "see files", sort_key="0", input_ids=[1], file_count=9)
    batches = pack([_unit(1, 100), with_files, _unit(2, 100)], max_chars=2 * FILE_CHARS)

    assert [len(b.units) for b in batches] == [1, 1, 1]
    assert with_files.weight == len(with_files.render()) + 9 * FILE_CHARS


def test_batches_are_written_as_numbered_files(tmp_path: Path) -> None:
    paths = write_batches(pack([_unit(1, 10)], 1000), tmp_path / "run", run_id=5)

    assert [p.name for p in paths] == ["batch-01.md"]
    assert "## unit 1" in paths[0].read_text(encoding="utf-8")

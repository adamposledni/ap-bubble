"""Packs units into batches of bounded size and writes each as a markdown file for Claude."""

from dataclasses import dataclass, field
from pathlib import Path

from bubble_core.clock import utc_now
from bubble_core.log import get_logger
from bubble_curator.unit import Unit, clip

logger = get_logger(__name__)


@dataclass
class Batch:
    units: list[Unit] = field(default_factory=list)
    weight: int = 0

    @property
    def input_ids(self) -> list[int]:
        return [i for unit in self.units for i in unit.input_ids]

    @property
    def item_count(self) -> int:
        return sum(len(unit.item_ids) for unit in self.units)


def pack(units: list[Unit], max_chars: int) -> list[Batch]:
    """Units in order, a new batch whenever the next unit would not fit; a huge unit is cut."""
    batches: list[Batch] = []
    for unit in units:
        unit = _fit(unit, max_chars)
        size = unit.weight
        if not batches or batches[-1].weight + size > max_chars:
            batches.append(Batch())
        batches[-1].units.append(unit)
        batches[-1].weight += size
    logger.debug("%d units packed into %d batches", len(units), len(batches))
    return batches


def write_batches(batches: list[Batch], run_dir: Path, run_id: int) -> list[Path]:
    run_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for number, batch in enumerate(batches, start=1):
        path = run_dir / f"batch-{number:02d}.md"
        header = f"# Curation batch {number} of {len(batches)} (run {run_id}, {utc_now()})\n\n"
        path.write_text(header + "\n".join(u.render() for u in batch.units), encoding="utf-8")
        paths.append(path)
    logger.info("Wrote %d batch files to %s", len(paths), run_dir)
    return paths


def _fit(unit: Unit, max_chars: int) -> Unit:
    room = max_chars - len(unit.heading) - 20
    if len(unit.render()) <= max_chars:
        return unit
    return Unit(
        unit.heading,
        clip(unit.body, room),
        unit.sort_key,
        unit.item_ids,
        unit.input_ids,
        unit.file_count,
    )

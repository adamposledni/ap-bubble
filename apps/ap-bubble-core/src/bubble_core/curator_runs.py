"""Reads the files of a curator run: its batch files and Claude's output per batch.

The curator writes `batch-NN.md` per batch and, after each Claude call, `batch-NN.out.json`
(Claude Code's JSON result) into `<runs dir>/<job run id>/`. Read only.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from bubble_core.log import get_logger
from bubble_core.paths import curator_runs_dir

BATCH_NAME = re.compile(r"^batch-\d{2,}\.md$")

logger = get_logger(__name__)


@dataclass(frozen=True)
class BatchInfo:
    name: str
    status: str  # done, failed, running, pending, not_sent (dry run)
    summary: str | None
    num_turns: int | None
    duration_seconds: float | None
    cost_usd: float | None


def batch_names(run_id: int) -> list[str]:
    """The batch files of a run, in order; empty when the run wrote none."""
    run_dir = curator_runs_dir() / str(run_id)
    if not run_dir.is_dir():
        return []
    return sorted(p.name for p in run_dir.iterdir() if BATCH_NAME.match(p.name))


def batches_of(run_id: int, run_status: str, dry_run: bool) -> list[BatchInfo]:
    """Every batch of a run with the state derived from its output file and the run's status."""
    names = batch_names(run_id)
    outputs = [_read_output(_output_path(run_id, name)) for name in names]
    blocked = False  # a failed or running batch holds the later ones back
    batches = []
    for name, output in zip(names, outputs, strict=True):
        status = _status(output, run_status, dry_run, blocked)
        blocked = blocked or status in ("failed", "running")
        batches.append(_info(name, status, output))
    return batches


def batch_text(run_id: int, name: str) -> str | None:
    """The content of one batch file; None for an unknown or invalid name."""
    if not BATCH_NAME.match(name):
        logger.warning("Rejected batch file name %r", name)
        return None
    path = curator_runs_dir() / str(run_id) / name
    return path.read_text(encoding="utf-8") if path.is_file() else None


def done_batches(run_id: int) -> int:
    return sum(1 for name in batch_names(run_id) if _output_path(run_id, name).is_file())


def _output_path(run_id: int, name: str) -> Path:
    return curator_runs_dir() / str(run_id) / name.replace(".md", ".out.json")


def _read_output(path: Path) -> dict | None:
    """The parsed output; {} when the file exists but is not valid JSON; None when missing."""
    if not path.is_file():
        return None
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("Unreadable curator output %s", path)
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _status(output: dict | None, run_status: str, dry_run: bool, blocked: bool) -> str:
    if dry_run:
        return "not_sent"
    if output is not None:
        return "failed" if output.get("is_error", True) else "done"
    if blocked or run_status == "succeeded":
        return "pending"
    return "running" if run_status == "running" else "failed"


def _info(name: str, status: str, output: dict | None) -> BatchInfo:
    output = output or {}
    duration_ms = output.get("duration_ms")
    return BatchInfo(
        name=name,
        status=status,
        summary=output.get("result"),
        num_turns=output.get("num_turns"),
        duration_seconds=duration_ms / 1000 if isinstance(duration_ms, int | float) else None,
        cost_usd=output.get("total_cost_usd"),
    )

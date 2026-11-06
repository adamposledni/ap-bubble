"""One curator run: gather inputs and L0 changes, write batches, let Claude curate them.

L0 progress (the cursor) moves only when every batch of the run succeeded; inputs are
'processing' while their batch runs, then 'done' or 'failed'. A dry run only writes the
batch files: no Claude call, no status or cursor change.
"""

import sqlite3
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from bubble_core.input_queue import queued_inputs, requeue_stuck, set_status
from bubble_core.job_log import JobRun, job_run
from bubble_core.log import get_logger
from bubble_core.paths import curator_runs_dir
from bubble_curator.batches import Batch, pack, write_batches
from bubble_curator.changes import ChangeSet, read_changes
from bubble_curator.claude import CurationFailed, curate_batch
from bubble_curator.cursor import load_position, save_position
from bubble_curator.selection import is_curatable, window_start
from bubble_curator.settings import (
    MAX_BATCH_CHARS,
    MAX_INPUTS_PER_RUN,
    MAX_ITEMS_PER_RUN,
    WINDOW_DAYS,
)
from bubble_curator.units import build_units, chat_titles

JOB_NAME = "curator.run"
DRY_RUN_JOB_NAME = "curator.dry_run"

logger = get_logger(__name__)


@dataclass(frozen=True)
class Options:
    dry_run: bool = False
    max_items: int = MAX_ITEMS_PER_RUN
    window_days: int = WINDOW_DAYS
    max_batch_chars: int = MAX_BATCH_CHARS


def run(conn: sqlite3.Connection, options: Options) -> None:
    with job_run(conn, DRY_RUN_JOB_NAME if options.dry_run else JOB_NAME) as job:
        if not options.dry_run:
            requeue_stuck(conn)
        inputs = queued_inputs(conn, MAX_INPUTS_PER_RUN)
        keep = partial(is_curatable, since=window_start(options.window_days))
        changes = read_changes(conn, load_position(conn), keep, options.max_items)
        units = build_units(inputs, changes.items, chat_titles(conn))
        if not units:
            _finish_without_work(conn, changes, options)
            return
        batches = pack(units, options.max_batch_chars)
        paths = write_batches(batches, curator_runs_dir() / str(job.id), job.id)
        job.items_processed = len(inputs) + len(changes.items)
        if options.dry_run:
            logger.info("Dry run: %d batches written, nothing curated", len(paths))
            return
        _curate(conn, batches, paths, job)
        if changes.end:
            save_position(conn, changes.end)


def _curate(conn: sqlite3.Connection, batches: list[Batch], paths: list[Path], job: JobRun) -> None:
    """Batch by batch; on a failure its inputs fail, later ones go back to the queue."""
    for index, (batch, path) in enumerate(zip(batches, paths, strict=True)):
        set_status(conn, batch.input_ids, "processing")
        try:
            summary = curate_batch(path)
        except CurationFailed as error:
            set_status(conn, batch.input_ids, "failed", str(error))
            later = [i for b in batches[index + 1 :] for i in b.input_ids]
            set_status(conn, later, "queued")
            raise
        set_status(conn, batch.input_ids, "done")
        logger.info("Batch %s done (%d items): %s", path.name, batch.item_count, summary[:200])
    logger.info("Run %d curated %d batches", job.id, len(batches))


def _finish_without_work(conn: sqlite3.Connection, changes: ChangeSet, options: Options) -> None:
    """Early exit, no Claude call; skipped rows still move the cursor (except in a dry run)."""
    if changes.end and not options.dry_run:
        save_position(conn, changes.end)
    logger.info("Nothing to curate (%d rows looked at)", changes.examined)

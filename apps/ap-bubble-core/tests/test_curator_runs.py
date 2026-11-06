import json
import sqlite3
from pathlib import Path

from bubble_core.curator_runs import batch_text, batches_of
from bubble_core.job_log import job_run
from bubble_core.paths import curator_runs_dir
from bubble_core.queries.job_runs import run_detail, running_jobs


def _write(run_id: int, name: str, content: str) -> Path:
    path = curator_runs_dir() / str(run_id) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _output(run_id: int, number: int, is_error: bool = False) -> None:
    result = {
        "result": "did it",
        "is_error": is_error,
        "num_turns": 4,
        "duration_ms": 2500,
        "total_cost_usd": 0.5,
    }
    _write(run_id, f"batch-{number:02d}.out.json", json.dumps(result))


def _batch_files(run_id: int, count: int) -> None:
    for number in range(1, count + 1):
        _write(run_id, f"batch-{number:02d}.md", "x")


def test_batches_of_a_running_run_are_done_running_pending() -> None:
    _batch_files(7, 3)
    _output(7, 1)

    batches = batches_of(7, "running", dry_run=False)

    assert [b.status for b in batches] == ["done", "running", "pending"]
    assert (batches[0].summary, batches[0].num_turns) == ("did it", 4)
    assert (batches[0].duration_seconds, batches[0].cost_usd) == (2.5, 0.5)


def test_failed_run_marks_the_failed_batch_and_holds_the_rest_back() -> None:
    _batch_files(8, 3)
    _output(8, 1)
    _output(8, 2, is_error=True)

    statuses = [b.status for b in batches_of(8, "failed", dry_run=False)]

    assert statuses == ["done", "failed", "pending"]


def test_dry_run_batches_are_not_sent() -> None:
    _batch_files(9, 1)

    assert [b.status for b in batches_of(9, "succeeded", dry_run=True)] == ["not_sent"]


def test_batch_text_only_serves_batch_files() -> None:
    _write(5, "batch-01.md", "# batch")
    _write(5, "knowledge-index.md", "secret")

    assert batch_text(5, "batch-01.md") == "# batch"
    assert batch_text(5, "knowledge-index.md") is None
    assert batch_text(5, "../5/batch-01.md") is None
    assert batch_text(6, "batch-01.md") is None


def test_running_curator_reports_batch_progress(conn: sqlite3.Connection) -> None:
    with job_run(conn, "curator.run") as run:
        _batch_files(run.id, 3)
        _output(run.id, 1)
        [running] = running_jobs(conn)

    assert (running.batch_current, running.batch_total) == (2, 3)


def test_run_detail_has_batches_for_curator_runs_only(conn: sqlite3.Connection) -> None:
    with job_run(conn, "curator.run") as curator_run:
        _batch_files(curator_run.id, 1)
    with job_run(conn, "ingest.gmail", "google:me@gmail.com") as ingest_run:
        pass

    curator = run_detail(conn, curator_run.id)
    ingest = run_detail(conn, ingest_run.id)

    assert curator is not None and [b.name for b in curator.batches] == ["batch-01.md"]
    assert ingest is not None and ingest.batches == []
    assert run_detail(conn, 999) is None

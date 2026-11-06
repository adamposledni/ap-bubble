import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from bubble_curator import claude
from bubble_curator.claude import CurationFailed, curate_batch


class FakeProcess:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.calls: list[dict[str, Any]] = []
        self.result = subprocess.CompletedProcess([], returncode, stdout, stderr)

    def __call__(self, command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append({"command": command, **kwargs})
        return self.result


@pytest.fixture
def batch(tmp_path: Path) -> Path:
    path = tmp_path / "batch-01.md"
    path.write_text("# batch", encoding="utf-8")
    return path


def _use(monkeypatch: pytest.MonkeyPatch, process: FakeProcess) -> None:
    monkeypatch.setattr(claude.shutil, "which", lambda name: f"/bin/{name}")
    monkeypatch.setattr(claude.subprocess, "run", process)


def test_claude_runs_in_the_knowledge_folder_with_file_tools_only(
    monkeypatch: pytest.MonkeyPatch, batch: Path
) -> None:
    process = FakeProcess(stdout=json.dumps({"is_error": False, "result": "done", "num_turns": 3}))
    _use(monkeypatch, process)

    assert curate_batch(batch) == "done"

    [call] = process.calls
    command = call["command"]
    assert command[command.index("--tools") + 1] == "Read,Write,Edit,Glob,Grep"
    assert command[command.index("--permission-mode") + 1] == "acceptEdits"
    assert str(batch) in command[command.index("-p") + 1]
    assert Path(call["cwd"]).name == "knowledge"
    assert batch.with_suffix(".out.json").exists()


def test_failures_raise_curation_failed(monkeypatch: pytest.MonkeyPatch, batch: Path) -> None:
    _use(monkeypatch, FakeProcess(returncode=1, stderr="boom"))
    with pytest.raises(CurationFailed, match="boom"):
        curate_batch(batch)

    _use(monkeypatch, FakeProcess(stdout=json.dumps({"is_error": True, "result": "limit"})))
    with pytest.raises(CurationFailed, match="limit"):
        curate_batch(batch)


def test_instructions_ship_with_the_package() -> None:
    assert "curator of Adam's knowledge base" in claude.instructions()

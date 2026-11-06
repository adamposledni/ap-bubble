import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from bubble_curator import claude
from bubble_curator.claude import CurationFailed, curate_batch, session_flags
from bubble_curator.settings import CLAUDE_EFFORT_ENV, CLAUDE_MODEL_ENV


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


def _value(command: list[str], flag: str) -> str:
    return command[command.index(flag) + 1]


def test_claude_runs_in_the_knowledge_folder_with_file_tools_only(
    monkeypatch: pytest.MonkeyPatch, batch: Path
) -> None:
    process = FakeProcess(stdout=json.dumps({"is_error": False, "result": "done", "num_turns": 3}))
    _use(monkeypatch, process)

    assert curate_batch(batch, batch.with_name("knowledge-index.md")) == "done"

    [call] = process.calls
    command = call["command"]
    assert _value(command, "--tools") == "Read,Write,Edit,Glob,Grep"
    assert _value(command, "--permission-mode") == "acceptEdits"
    assert str(batch) in _value(command, "-p") and "knowledge-index.md" in _value(command, "-p")
    assert Path(call["cwd"]).name == "knowledge"
    assert batch.with_suffix(".out.json").exists()


def test_session_is_lean_with_a_fixed_model_and_effort() -> None:
    flags = session_flags()

    assert (_value(flags, "--model"), _value(flags, "--effort")) == ("claude-opus-5-5", "medium")
    assert json.loads(_value(flags, "--mcp-config")) == {"mcpServers": {}}
    assert "--strict-mcp-config" in flags and "--disable-slash-commands" in flags
    assert _value(flags, "--setting-sources") == "project,local"


def test_model_and_effort_can_be_overridden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(CLAUDE_MODEL_ENV, "claude-sonnet-5-5")
    monkeypatch.setenv(CLAUDE_EFFORT_ENV, "low")

    flags = session_flags()

    assert (_value(flags, "--model"), _value(flags, "--effort")) == ("claude-sonnet-5-5", "low")


def test_failures_raise_curation_failed(monkeypatch: pytest.MonkeyPatch, batch: Path) -> None:
    index = batch.with_name("knowledge-index.md")
    _use(monkeypatch, FakeProcess(returncode=1, stderr="boom"))
    with pytest.raises(CurationFailed, match="boom"):
        curate_batch(batch, index)

    _use(monkeypatch, FakeProcess(stdout=json.dumps({"is_error": True, "result": "limit"})))
    with pytest.raises(CurationFailed, match="limit"):
        curate_batch(batch, index)

    result = json.dumps({"is_error": True, "result": "model needs a newer version"})
    _use(monkeypatch, FakeProcess(returncode=1, stdout=result))
    with pytest.raises(CurationFailed, match="newer version"):
        curate_batch(batch, index)


def test_instructions_ship_with_the_package() -> None:
    assert "curator of Adam's knowledge base" in claude.instructions()

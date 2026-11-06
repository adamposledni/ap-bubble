"""Runs Claude Code headless on one batch file, inside the knowledge folder.

Claude may only read and edit files (no shell, no web); edits are accepted automatically.
The session is lean: a fixed model and effort, no MCP servers, no user settings (plugins,
hooks), no skills. Its JSON result is saved next to the batch file.
"""

import json
import os
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path

from bubble_core.log import get_logger
from bubble_core.paths import inbox_dir, knowledge_dir
from bubble_curator.settings import (
    CLAUDE_COMMAND_ENV,
    CLAUDE_EFFORT,
    CLAUDE_EFFORT_ENV,
    CLAUDE_MODEL,
    CLAUDE_MODEL_ENV,
    CLAUDE_TIMEOUT_SECONDS,
)

TOOLS = "Read,Write,Edit,Glob,Grep"
_NO_MCP_SERVERS = json.dumps({"mcpServers": {}})
_PROMPT = (
    "Curate the batch file {batch}. The existing knowledge files are listed in {index}. "
    "Update the knowledge files in the current folder following your instructions, then "
    "finish with a short summary of what you changed."
)
_ERROR_TAIL = 500

logger = get_logger(__name__)


class CurationFailed(Exception):
    """Claude could not curate a batch; the run stops and nothing is marked done."""


def curate_batch(batch_file: Path, index_file: Path) -> str:
    """Run Claude on the batch; return its summary. Raises CurationFailed."""
    command = [executable(), "-p", _PROMPT.format(batch=batch_file, index=index_file)]
    command += _curation_flags(batch_file.parent) + session_flags()
    logger.info("Curating %s with Claude", batch_file.name)
    try:
        completed = subprocess.run(
            command,
            cwd=knowledge_dir(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=CLAUDE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise CurationFailed(f"Claude timed out after {CLAUDE_TIMEOUT_SECONDS} s") from error
    batch_file.with_suffix(".out.json").write_text(completed.stdout, encoding="utf-8")
    return _summary(completed)


def session_flags() -> list[str]:
    """Model, effort and a lean session; shared by curation and the smoke test."""
    return [
        "--model",
        os.environ.get(CLAUDE_MODEL_ENV, CLAUDE_MODEL),
        "--effort",
        os.environ.get(CLAUDE_EFFORT_ENV, CLAUDE_EFFORT),
        "--strict-mcp-config",
        "--mcp-config",
        _NO_MCP_SERVERS,
        "--setting-sources",
        "project,local",
        "--disable-slash-commands",
        "--exclude-dynamic-system-prompt-sections",
        "--output-format",
        "json",
        "--no-session-persistence",
    ]


def executable() -> str:
    found = shutil.which(os.environ.get(CLAUDE_COMMAND_ENV, "claude"))
    if found is None:
        raise CurationFailed("Claude Code CLI not found; install it or set " + CLAUDE_COMMAND_ENV)
    return found


def instructions() -> str:
    return (files("bubble_curator") / "prompts" / "curate.md").read_text(encoding="utf-8")


def _curation_flags(run_dir: Path) -> list[str]:
    """File tools only, edits accepted; the run folder and the inbox are readable too."""
    return [
        "--tools",
        TOOLS,
        "--permission-mode",
        "acceptEdits",
        "--add-dir",
        str(run_dir),
        "--add-dir",
        str(inbox_dir()),
        "--append-system-prompt",
        instructions(),
    ]


def _summary(completed: subprocess.CompletedProcess[str]) -> str:
    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout)[-_ERROR_TAIL:]
        raise CurationFailed(f"Claude exited with {completed.returncode}: {tail}")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise CurationFailed("Claude returned no JSON result") from error
    if result.get("is_error"):
        raise CurationFailed(f"Claude reported an error: {str(result.get('result'))[:_ERROR_TAIL]}")
    logger.info("Claude finished in %s turns", result.get("num_turns", "?"))
    return str(result.get("result", ""))

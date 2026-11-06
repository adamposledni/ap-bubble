"""An index of the existing knowledge files (path, name, aliases, emails), written before each
batch, so Claude finds the right file without searching the whole knowledge base."""

from pathlib import Path

from bubble_core.knowledge import KnowledgeFile, list_files
from bubble_core.log import get_logger

logger = get_logger(__name__)


def write_index(path: Path) -> int:
    """Write the index to path; return how many files it lists."""
    files = list_files()
    lines = [_line(file) for file in files]
    header = "# Existing knowledge files\n\npath — name (aliases; emails)\n\n"
    path.write_text(header + ("\n".join(lines) or "(none yet)") + "\n", encoding="utf-8")
    logger.debug("Knowledge index lists %d files", len(files))
    return len(files)


def _line(file: KnowledgeFile) -> str:
    lists = (file.meta.aliases, file.meta.emails)
    extra = "; ".join(", ".join(values) for values in lists if values)
    return f"- {file.ref}.md — {file.meta.name}" + (f" ({extra})" if extra else "")

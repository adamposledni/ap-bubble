"""An index of the existing knowledge files (path, name, aliases, emails), written before each
batch, so Claude finds the right file without searching the whole knowledge base."""

from pathlib import Path

from bubble_core.log import get_logger
from bubble_core.paths import knowledge_dir

FOLDERS = ("people", "places", "topics", "me")
_FIELDS = ("aliases", "emails")

logger = get_logger(__name__)


def write_index(path: Path) -> int:
    """Write the index to path; return how many files it lists."""
    root = knowledge_dir()
    files = [f for folder in FOLDERS for f in sorted((root / folder).glob("*.md"))]
    lines = [_line(root, f) for f in files]
    header = "# Existing knowledge files\n\npath — name (aliases; emails)\n\n"
    path.write_text(header + ("\n".join(lines) or "(none yet)") + "\n", encoding="utf-8")
    logger.debug("Knowledge index lists %d files", len(files))
    return len(files)


def _line(root: Path, file: Path) -> str:
    meta = front_matter(file.read_text(encoding="utf-8", errors="replace"))
    extra = "; ".join(meta[field] for field in _FIELDS if meta.get(field))
    name = meta.get("name") or file.stem
    return f"- {file.relative_to(root).as_posix()} — {name}" + (f" ({extra})" if extra else "")


def front_matter(text: str) -> dict[str, str]:
    """Top-level 'key: value' lines of the YAML front matter; [a, b] lists become 'a, b'."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, value = line.partition(":")
        if separator and not line.startswith((" ", "-")):
            meta[key.strip()] = value.strip().strip("[]").strip()
    return meta

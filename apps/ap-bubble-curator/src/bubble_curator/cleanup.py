"""Removes knowledge files Claude marked for deletion (merged, renamed, duplicates).

Claude has no tool to delete files, so it marks them with `deleted: true` in the front matter;
the curator removes them after each batch.
"""

from pathlib import Path

from bubble_core.knowledge import FOLDERS, front_matter
from bubble_core.log import get_logger
from bubble_core.paths import knowledge_dir

logger = get_logger(__name__)


def remove_deleted_files() -> list[str]:
    """Delete every knowledge file marked `deleted: true`; return their refs (people/x)."""
    root = knowledge_dir()
    removed = [_remove(root, path) for path in _marked_files(root)]
    logger.debug("Removed %d knowledge files marked deleted", len(removed))
    return removed


def _marked_files(root: Path) -> list[Path]:
    paths = (path for folder in FOLDERS for path in sorted((root / folder).glob("*.md")))
    return [path for path in paths if _is_marked(path)]


def _is_marked(path: Path) -> bool:
    meta = front_matter(path.read_text(encoding="utf-8", errors="replace"))
    return meta.get("deleted", "").lower() == "true"


def _remove(root: Path, path: Path) -> str:
    ref = path.relative_to(root).with_suffix("").as_posix()
    path.unlink()
    logger.info("Removed knowledge file %s (marked deleted)", ref)
    return ref

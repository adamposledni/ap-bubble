"""Reading knowledge files; only <folder>/<slug>.md files of the knowledge folder are reachable."""

import re
from pathlib import Path

from bubble_core.knowledge.front_matter import split_front_matter
from bubble_core.knowledge.model import FOLDERS, Folder, KnowledgeFile, meta_from
from bubble_core.log import get_logger
from bubble_core.paths import knowledge_dir

# No path separators and no leading dot: a slug can never leave its folder.
_SLUG = re.compile(r"\w[\w.-]*")

logger = get_logger(__name__)


class KnowledgeNotFound(Exception):
    pass


def list_files(folder: Folder | None = None) -> list[KnowledgeFile]:
    """Every knowledge file, or those of one folder (questions.md in the root is not one)."""
    files = [load_file(name, path) for name, path in file_paths(folder)]
    logger.debug("Read %d knowledge files (folder %s)", len(files), folder or "all")
    return files


def file_paths(folder: Folder | None = None) -> list[tuple[Folder, Path]]:
    """(folder, path) of every knowledge file, or of those of one folder, without reading them."""
    root = knowledge_dir()
    folders = FOLDERS if folder is None else (folder,)
    return [(name, path) for name in folders for path in sorted((root / name).glob("*.md"))]


def read_file(folder: Folder, slug: str) -> KnowledgeFile:
    path = _path(folder, slug)
    if not path.is_file():
        raise KnowledgeNotFound(f"No knowledge file {folder}/{slug}")
    return load_file(folder, path)


def _path(folder: str, slug: str) -> Path:
    if folder not in FOLDERS or not _SLUG.fullmatch(slug):
        logger.warning("Rejected knowledge path %r/%r", folder, slug)
        raise KnowledgeNotFound(f"No knowledge file {folder}/{slug}")
    return knowledge_dir() / folder / f"{slug}.md"


def load_file(folder: Folder, path: Path) -> KnowledgeFile:
    logger.trace("Reading %s", path)
    raw, body = split_front_matter(path.read_text(encoding="utf-8", errors="replace"))
    return KnowledgeFile(folder=folder, slug=path.stem, meta=meta_from(raw, path.stem), body=body)

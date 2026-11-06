"""Relative markdown links between knowledge files, and the backlinks they give."""

import posixpath
import re
from urllib.parse import unquote

from bubble_core.knowledge.model import FOLDERS, KnowledgeFile, KnowledgeRef, ref_of
from bubble_core.log import get_logger

_LINK_TARGET = re.compile(r"\]\(\s*([^)\s#]+\.md)(?:#[^)\s]*)?\s*\)")

logger = get_logger(__name__)


def resolve_link(folder: str, href: str) -> str | None:
    """'people/petr-novak' for a link like '../people/petr-novak.md' in a file of folder."""
    if "://" in href or href.startswith("/"):
        return None
    path = posixpath.normpath(posixpath.join(folder, unquote(href)))
    target_folder, _, name = path.partition("/")
    if target_folder not in FOLDERS or "/" in name or not name.endswith(".md"):
        return None
    return path.removesuffix(".md")


def linked_refs(file: KnowledgeFile) -> set[str]:
    """Refs ('folder/slug') of the knowledge files that file links to."""
    hrefs = _LINK_TARGET.findall(file.body)
    return {ref for href in hrefs if (ref := resolve_link(file.folder, href))}


def backlinks(target: KnowledgeFile, files: list[KnowledgeFile]) -> list[KnowledgeRef]:
    """The other files linking to target, by name."""
    sources = [f for f in files if f.ref != target.ref and target.ref in linked_refs(f)]
    logger.debug("%s has %d backlinks", target.ref, len(sources))
    return sorted((ref_of(f) for f in sources), key=lambda ref: ref.name.casefold())

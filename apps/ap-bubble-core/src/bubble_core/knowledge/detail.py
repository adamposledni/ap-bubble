"""One knowledge file with the files that mention it."""

from dataclasses import dataclass

from bubble_core.knowledge.files import list_files, read_file
from bubble_core.knowledge.links import backlinks
from bubble_core.knowledge.model import Folder, KnowledgeMeta, KnowledgeRef


@dataclass(frozen=True)
class KnowledgeDoc:
    folder: Folder
    slug: str
    meta: KnowledgeMeta
    body: str  # markdown
    backlinks: list[KnowledgeRef]


def knowledge_doc(folder: Folder, slug: str) -> KnowledgeDoc:
    """Raises KnowledgeNotFound for anything but an existing <folder>/<slug>.md."""
    file = read_file(folder, slug)
    return KnowledgeDoc(
        folder=file.folder,
        slug=file.slug,
        meta=file.meta,
        body=file.body,
        backlinks=backlinks(file, list_files()),
    )

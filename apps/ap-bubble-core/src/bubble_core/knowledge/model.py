"""Read models of the L2 knowledge files (markdown with front matter, see the curator prompt)."""

from dataclasses import dataclass
from typing import Literal, get_args

from bubble_core.knowledge.front_matter import list_value, unquote

Folder = Literal["people", "places", "topics", "me"]
FOLDERS: tuple[Folder, ...] = get_args(Folder)


@dataclass(frozen=True)
class KnowledgeMeta:
    name: str
    aliases: list[str]
    emails: list[str]
    phones: list[str]
    tags: list[str]
    updated: str | None  # YYYY-MM-DD


@dataclass(frozen=True)
class KnowledgeFile:
    folder: Folder
    slug: str  # file name without .md
    meta: KnowledgeMeta
    body: str  # markdown after the front matter

    @property
    def ref(self) -> str:
        """'people/petr-novak': how links and backlinks name the file."""
        return f"{self.folder}/{self.slug}"


@dataclass(frozen=True)
class KnowledgeRef:
    folder: Folder
    slug: str
    name: str


def meta_from(raw: dict[str, str], slug: str) -> KnowledgeMeta:
    """Meta of a file from its raw front matter; the name falls back to the slug."""
    return KnowledgeMeta(
        name=unquote(raw.get("name", "")) or slug,
        aliases=list_value(raw.get("aliases")),
        emails=list_value(raw.get("emails")),
        phones=list_value(raw.get("phones")),
        tags=list_value(raw.get("tags")),
        updated=unquote(raw.get("updated", "")) or None,
    )


def ref_of(file: KnowledgeFile) -> KnowledgeRef:
    return KnowledgeRef(folder=file.folder, slug=file.slug, name=file.meta.name)

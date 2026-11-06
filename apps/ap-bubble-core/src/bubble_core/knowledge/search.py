"""Keyword search over the knowledge files, scanning them on each call.

Every word of the query must match (folded, as a substring) the name/aliases, the
tags/emails/phones or the body; files whose words match in the name rank first.
"""

from dataclasses import dataclass

from bubble_core.knowledge.files import list_files
from bubble_core.knowledge.fold import fold
from bubble_core.knowledge.model import Folder, KnowledgeFile
from bubble_core.knowledge.plain import plain_text
from bubble_core.knowledge.snippet import SnippetPart, snippet
from bubble_core.log import get_logger

MAX_RESULTS = 100
_NAME, _META, _BODY = 3, 2, 1  # weight of a word matching in that field

logger = get_logger(__name__)


@dataclass(frozen=True)
class SearchHit:
    folder: Folder
    slug: str
    name: str
    tags: list[str]
    updated: str | None
    snippet: list[SnippetPart]


@dataclass(frozen=True)
class SearchResult:
    total: int  # all matching files; hits holds at most the limit
    hits: list[SearchHit]


@dataclass(frozen=True)
class _Candidate:
    file: KnowledgeFile
    plain: str
    fields: tuple[tuple[int, str], ...]  # (weight, folded text)


def search(query: str, folder: Folder | None = None, limit: int = MAX_RESULTS) -> SearchResult:
    """Matching files, best first; an empty query lists all, most recently updated first."""
    terms = fold(query).split()
    scored = [
        (score, c) for c in map(_candidate, list_files(folder)) if (score := _score(c, terms))
    ]
    ranked = _ranked(scored)
    logger.debug("Search %r in %s: %d matches", query, folder or "all", len(ranked))
    return SearchResult(total=len(ranked), hits=[_hit(c, terms) for c in ranked[:limit]])


def _candidate(file: KnowledgeFile) -> _Candidate:
    meta = file.meta
    plain = plain_text(file.body)
    names = " ".join([meta.name, *meta.aliases, file.slug])
    details = " ".join([*meta.tags, *meta.emails, *meta.phones])
    fields = ((_NAME, fold(names)), (_META, fold(details)), (_BODY, fold(plain)))
    return _Candidate(file=file, plain=plain, fields=fields)


def _score(candidate: _Candidate, terms: list[str]) -> int | None:
    """Sum of each word's best field weight; None when a word matches nowhere."""
    total = 0
    for term in terms:
        weight = max((w for w, text in candidate.fields if term in text), default=0)
        if not weight:
            return None
        total += weight
    return total if terms else 1  # every file matches an empty query


def _ranked(scored: list[tuple[int, _Candidate]]) -> list[_Candidate]:
    """By score, then updated (newest first), then name (stable sorts, last key first)."""
    by_name = sorted(scored, key=lambda pair: fold(pair[1].file.meta.name))
    by_updated = sorted(by_name, key=lambda pair: pair[1].file.meta.updated or "", reverse=True)
    return [candidate for _, candidate in sorted(by_updated, key=lambda pair: -pair[0])]


def _hit(candidate: _Candidate, terms: list[str]) -> SearchHit:
    file = candidate.file
    return SearchHit(
        folder=file.folder,
        slug=file.slug,
        name=file.meta.name,
        tags=file.meta.tags,
        updated=file.meta.updated,
        snippet=snippet(candidate.plain, terms),
    )

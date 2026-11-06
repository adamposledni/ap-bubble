"""Keyword search over the knowledge files through their SQLite full-text index.

Every word of the query must start a word (folded) of the name/aliases/slug, the
tags/emails/phones or the body; matches in the names rank first, the body last.
"""

import json
import re
import sqlite3
from dataclasses import dataclass

from bubble_core.knowledge.fold import fold
from bubble_core.knowledge.index import sync_index
from bubble_core.knowledge.model import Folder
from bubble_core.knowledge.snippet import SnippetPart, snippet
from bubble_core.log import get_logger

MAX_RESULTS = 100

# A word without a letter or digit makes no full-text token, so it cannot match; it is ignored.
_WORD = re.compile(r"[^\W_]")
_COLUMNS = "f.folder, f.slug, f.name, f.tags, f.updated, f.plain, COUNT(*) OVER () AS total"
_IN_FOLDER = "(:folder IS NULL OR f.folder = :folder)"
# bm25 (weights of names, details, body; lower is better) cannot share a SELECT with COUNT OVER.
_MATCH_SQL = f"""
    WITH matches AS MATERIALIZED (
        SELECT rowid AS id, bm25(l2_knowledge_fts, 10, 5, 1) AS score
        FROM l2_knowledge_fts
        WHERE l2_knowledge_fts MATCH :match
    )
    SELECT {_COLUMNS}
    FROM matches JOIN l2_knowledge_files AS f ON f.id = matches.id
    WHERE {_IN_FOLDER}
    ORDER BY matches.score, f.updated DESC, f.name_key
    LIMIT :limit
"""
_ALL_SQL = f"""
    SELECT {_COLUMNS}
    FROM l2_knowledge_files AS f
    WHERE {_IN_FOLDER}
    ORDER BY f.updated DESC, f.name_key
    LIMIT :limit
"""

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


def search(
    conn: sqlite3.Connection, query: str, folder: Folder | None = None, limit: int = MAX_RESULTS
) -> SearchResult:
    """Matching files, best first; an empty query lists all, most recently updated first."""
    sync_index(conn)
    terms = _terms(query)
    rows = _rows(conn, terms, {"folder": folder, "limit": limit})
    total = rows[0]["total"] if rows else 0
    logger.debug("Search %r in %s: %d matches", query, folder or "all", total)
    return SearchResult(total=total, hits=[_hit(row, terms) for row in rows])


def _terms(query: str) -> list[str]:
    """The folded words of the query that can match a full-text token."""
    return [word for word in fold(query).split() if _WORD.search(word)]


def _match_expression(terms: list[str]) -> str:
    """FTS5 query: every term as a quoted prefix ('"novak"*'), all of them required."""
    return " AND ".join('"{}"*'.format(term.replace('"', '""')) for term in terms)


def _rows(
    conn: sqlite3.Connection, terms: list[str], params: dict[str, object]
) -> list[sqlite3.Row]:
    if not terms:
        return conn.execute(_ALL_SQL, params).fetchall()
    match = _match_expression(terms)
    logger.trace("Full-text match %r", match)
    try:
        return conn.execute(_MATCH_SQL, {**params, "match": match}).fetchall()
    except sqlite3.OperationalError as error:  # a query FTS5 cannot parse matches nothing
        logger.warning("Full-text query %r failed: %s", match, error)
        return []


def _hit(row: sqlite3.Row, terms: list[str]) -> SearchHit:
    return SearchHit(
        folder=row["folder"],
        slug=row["slug"],
        name=row["name"],
        tags=json.loads(row["tags"]),
        updated=row["updated"],
        snippet=snippet(row["plain"], terms),
    )

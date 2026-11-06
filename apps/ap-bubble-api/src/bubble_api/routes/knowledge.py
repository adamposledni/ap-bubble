"""L2 knowledge: indexed keyword search over the files and one file with its backlinks."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from bubble_api.deps import Conn
from bubble_api.models import KnowledgeDocOut, KnowledgeSearchOut
from bubble_core.knowledge import MAX_RESULTS, Folder, KnowledgeNotFound, knowledge_doc, search

_MAX_LIMIT = 500

router = APIRouter(prefix="/knowledge")


@router.get("")
def search_knowledge(
    conn: Conn,
    q: str = "",
    folder: Folder | None = None,
    limit: Annotated[int, Query(ge=1, le=_MAX_LIMIT)] = MAX_RESULTS,
) -> KnowledgeSearchOut:
    """Files with a word starting with each word of q (all files when empty), best first."""
    return KnowledgeSearchOut.model_validate(search(conn, q, folder, limit))


@router.get("/{folder}/{slug}")
def get_knowledge_doc(folder: Folder, slug: str) -> KnowledgeDocOut:
    try:
        return KnowledgeDocOut.model_validate(knowledge_doc(folder, slug))
    except KnowledgeNotFound as error:
        raise HTTPException(404, str(error)) from error

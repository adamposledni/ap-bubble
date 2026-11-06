"""L2 knowledge files: parsing, keyword search and backlinks (no index; files are scanned)."""

from bubble_core.knowledge.detail import KnowledgeDoc, knowledge_doc
from bubble_core.knowledge.files import KnowledgeNotFound, list_files, read_file
from bubble_core.knowledge.front_matter import front_matter
from bubble_core.knowledge.model import FOLDERS, Folder, KnowledgeFile, KnowledgeMeta, KnowledgeRef
from bubble_core.knowledge.search import MAX_RESULTS, SearchHit, SearchResult, search

__all__ = [
    "FOLDERS",
    "MAX_RESULTS",
    "Folder",
    "KnowledgeDoc",
    "KnowledgeFile",
    "KnowledgeMeta",
    "KnowledgeNotFound",
    "KnowledgeRef",
    "SearchHit",
    "SearchResult",
    "front_matter",
    "knowledge_doc",
    "list_files",
    "read_file",
    "search",
]

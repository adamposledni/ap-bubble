"""Microsoft To Do over Graph v1.0: task lists and the (changed) tasks of a list."""

from dataclasses import dataclass
from urllib.parse import quote

import requests

from bubble_core.log import get_logger
from bubble_ingest.microsoft.graph import GRAPH_URL, Json, get_all_pages, get_delta

logger = get_logger(__name__)


@dataclass(frozen=True)
class TaskChanges:
    tasks: list[Json]
    delta_link: str  # where the next sync of the list starts


def list_tasklists(session: requests.Session) -> list[Json]:
    """Every task list of mine, built-in ones (Tasks, Flagged email) included."""
    tasklists = get_all_pages(session, f"{GRAPH_URL}/me/todo/lists").items
    logger.debug("Fetched %d To Do lists", len(tasklists))
    return tasklists


def task_changes(
    session: requests.Session, tasklist_id: str, delta_link: str | None
) -> TaskChanges:
    """Tasks changed since delta_link (removed ones carry @removed), or all tasks when None.

    Raises CursorExpired when Graph no longer accepts the delta link.
    """
    url = f"{GRAPH_URL}/me/todo/lists/{quote(tasklist_id, safe='=')}/tasks/delta"
    pages = get_delta(session, url, None, delta_link)
    if not pages.delta_link:
        raise RuntimeError(f"Graph returned no delta link for To Do list {tasklist_id}")
    logger.debug("Fetched %d changed tasks of To Do list %s", len(pages.items), tasklist_id)
    return TaskChanges(pages.items, pages.delta_link)

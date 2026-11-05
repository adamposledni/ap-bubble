"""Google Tasks API v1 over plain HTTP: task lists and their (changed) tasks."""

from typing import Any
from urllib.parse import quote

from google.auth.transport.requests import AuthorizedSession

from bubble_core.log import get_logger
from bubble_ingest.google.http import Json, get_all_pages

BASE_URL = "https://tasks.googleapis.com/tasks/v1"
_TASKLISTS_PAGE_SIZE = 1000  # API maximum
_TASKS_PAGE_SIZE = 100  # API maximum
# Completed tasks cleared in Google's apps are hidden; assigned ones come from Docs or Chat.
_SHOW_ALL = {
    "showCompleted": "true",
    "showHidden": "true",
    "showDeleted": "true",
    "showAssigned": "true",
}

logger = get_logger(__name__)


def list_tasklists(session: AuthorizedSession) -> list[Json]:
    url = f"{BASE_URL}/users/@me/lists"
    tasklists, _ = get_all_pages(session, url, {"maxResults": _TASKLISTS_PAGE_SIZE})
    logger.debug("Fetched %d task lists", len(tasklists))
    return tasklists


def list_tasks(session: AuthorizedSession, tasklist_id: str, updated_min: str | None) -> list[Json]:
    """Tasks modified since updated_min (RFC 3339), or all tasks of the list when it is None.

    Completed, hidden, deleted and assigned tasks are included.
    """
    params: dict[str, Any] = {"maxResults": _TASKS_PAGE_SIZE, **_SHOW_ALL}
    if updated_min:
        params["updatedMin"] = updated_min
    url = f"{BASE_URL}/lists/{quote(tasklist_id, safe='')}/tasks"
    tasks, _ = get_all_pages(session, url, params)
    logger.debug("Fetched %d tasks of list %s since %s", len(tasks), tasklist_id, updated_min)
    return tasks

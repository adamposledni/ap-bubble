"""Microsoft Planner over Graph v1.0: the tasks assigned to me and the plans they sit in."""

from urllib.parse import quote

import requests

from bubble_core.log import get_logger
from bubble_ingest.microsoft.graph import GRAPH_URL, Json, get_all_pages, get_json

# Planner answers these when a plan cannot be read, e.g. after leaving its group.
_UNREADABLE_STATUSES = {403, 404}

logger = get_logger(__name__)


def list_my_tasks(session: requests.Session) -> list[Json]:
    """Every task assigned to me, completed ones included (v1.0 has no Planner delta)."""
    tasks = get_all_pages(session, f"{GRAPH_URL}/me/planner/tasks").items
    logger.debug("Fetched %d Planner tasks", len(tasks))
    return tasks


def get_plan(session: requests.Session, plan_id: str) -> Json | None:
    """The plan, or None when Planner does not let me read it."""
    try:
        return get_json(session, f"{GRAPH_URL}/planner/plans/{quote(plan_id, safe='')}")
    except requests.HTTPError as error:
        status = error.response.status_code if error.response is not None else None
        if status not in _UNREADABLE_STATUSES:
            raise
        logger.warning(
            "Plan %s cannot be read (HTTP %s); saving it without a title", plan_id, status
        )
        return None

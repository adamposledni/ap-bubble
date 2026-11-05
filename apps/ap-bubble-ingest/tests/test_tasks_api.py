from typing import Any

import pytest

from bubble_ingest.google.tasks import api


@pytest.fixture
def requests_made(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, dict[str, Any]]]:
    """Records (url, params) of every paged GET and answers with one task."""
    made: list[tuple[str, dict[str, Any]]] = []

    def fake_get_all_pages(
        session: object, url: str, params: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        made.append((url, params))
        return [{"id": "t1"}], {}

    monkeypatch.setattr(api, "get_all_pages", fake_get_all_pages)
    return made


def test_full_load_asks_for_every_task_of_the_list(
    requests_made: list[tuple[str, dict[str, Any]]],
) -> None:
    tasks = api.list_tasks(object(), "list/1", None)

    assert tasks == [{"id": "t1"}]
    url, params = requests_made[0]
    assert url == f"{api.BASE_URL}/lists/list%2F1/tasks"
    assert params == {
        "maxResults": 100,
        "showCompleted": "true",
        "showHidden": "true",
        "showDeleted": "true",
        "showAssigned": "true",
    }


def test_incremental_load_asks_for_tasks_updated_since_cursor(
    requests_made: list[tuple[str, dict[str, Any]]],
) -> None:
    api.list_tasks(object(), "list1", "2026-11-05T10:00:00Z")

    _, params = requests_made[0]
    assert params["updatedMin"] == "2026-11-05T10:00:00Z"
    assert params["showDeleted"] == "true"

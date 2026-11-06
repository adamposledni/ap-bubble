from typing import Any

import pytest
import requests

from bubble_ingest.microsoft.graph import GRAPH_URL, Pages
from bubble_ingest.microsoft.planner import api


def _http_error(status: int) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status
    return requests.HTTPError(response=response)


def _failing_get_json(status: int):
    def get_json(session: object, url: str) -> dict[str, Any]:
        raise _http_error(status)

    return get_json


def test_my_tasks_come_from_my_planner(monkeypatch: pytest.MonkeyPatch) -> None:
    urls: list[str] = []

    def fake_get_all_pages(session: object, url: str) -> Pages:
        urls.append(url)
        return Pages([{"id": "t1"}], None)

    monkeypatch.setattr(api, "get_all_pages", fake_get_all_pages)

    assert api.list_my_tasks(object()) == [{"id": "t1"}]  # type: ignore[arg-type]
    assert urls == [f"{GRAPH_URL}/me/planner/tasks"]


def test_plan_is_read_by_id(monkeypatch: pytest.MonkeyPatch) -> None:
    urls: list[str] = []

    def fake_get_json(session: object, url: str) -> dict[str, Any]:
        urls.append(url)
        return {"id": "p1", "title": "Plan"}

    monkeypatch.setattr(api, "get_json", fake_get_json)

    assert api.get_plan(object(), "p1") == {"id": "p1", "title": "Plan"}  # type: ignore[arg-type]
    assert urls == [f"{GRAPH_URL}/planner/plans/p1"]


@pytest.mark.parametrize("status", [403, 404])
def test_unreadable_plan_is_none(monkeypatch: pytest.MonkeyPatch, status: int) -> None:
    monkeypatch.setattr(api, "get_json", _failing_get_json(status))

    assert api.get_plan(object(), "p1") is None  # type: ignore[arg-type]


def test_other_plan_errors_are_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api, "get_json", _failing_get_json(500))

    with pytest.raises(requests.HTTPError):
        api.get_plan(object(), "p1")  # type: ignore[arg-type]

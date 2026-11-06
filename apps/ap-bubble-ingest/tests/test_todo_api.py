from typing import Any

import pytest

from bubble_ingest.microsoft.graph import GRAPH_URL, Pages
from bubble_ingest.microsoft.todo import api


class FakeGraph:
    """Records (url, params, delta_link) of delta calls and answers with one scripted page set."""

    def __init__(self, delta_link: str | None) -> None:
        self.delta_link = delta_link
        self.calls: list[tuple[str, Any, str | None]] = []

    def get_delta(self, session: object, url: str, params: Any, delta_link: str | None) -> Pages:
        self.calls.append((url, params, delta_link))
        return Pages([{"id": "t1"}], self.delta_link)


def test_task_lists_come_from_my_todo(monkeypatch: pytest.MonkeyPatch) -> None:
    urls: list[str] = []

    def fake_get_all_pages(session: object, url: str) -> Pages:
        urls.append(url)
        return Pages([{"id": "l1"}], None)

    monkeypatch.setattr(api, "get_all_pages", fake_get_all_pages)

    assert api.list_tasklists(object()) == [{"id": "l1"}]  # type: ignore[arg-type]
    assert urls == [f"{GRAPH_URL}/me/todo/lists"]


def test_full_load_starts_a_delta_round_of_the_list(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = FakeGraph("https://delta")
    monkeypatch.setattr(api, "get_delta", graph.get_delta)

    changes = api.task_changes(object(), "AAk/x==", None)  # type: ignore[arg-type]

    assert (changes.tasks, changes.delta_link) == ([{"id": "t1"}], "https://delta")
    assert graph.calls == [(f"{GRAPH_URL}/me/todo/lists/AAk%2Fx==/tasks/delta", None, None)]


def test_next_load_follows_the_delta_link(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = FakeGraph("https://delta-2")
    monkeypatch.setattr(api, "get_delta", graph.get_delta)

    api.task_changes(object(), "l1", "https://delta-1")  # type: ignore[arg-type]

    assert graph.calls[0][2] == "https://delta-1"


def test_missing_delta_link_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api, "get_delta", FakeGraph(None).get_delta)

    with pytest.raises(RuntimeError, match="no delta link"):
        api.task_changes(object(), "l1", None)  # type: ignore[arg-type]

from collections.abc import Iterator
from itertools import islice
from typing import Any

import pytest

from bubble_ingest.microsoft import graph
from bubble_ingest.microsoft.chats import api

PREFER = {"Prefer": "include-unknown-enum-members"}


def test_messages_are_asked_for_by_last_modification_since_the_cursor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    made: list[tuple[str, Any, Any]] = []

    def fake_get_all_pages(session: object, url: str, params: Any, headers: Any) -> graph.Pages:
        made.append((url, params, headers))
        return graph.Pages([{"id": "m1"}], None)

    monkeypatch.setattr(api, "get_all_pages", fake_get_all_pages)

    messages = api.list_messages(object(), "19:c1@thread.v2", "2026-03-05T09:30:00.12Z")  # type: ignore[arg-type]

    assert messages == [{"id": "m1"}]
    assert made == [
        (
            f"{graph.GRAPH_URL}/me/chats/19:c1@thread.v2/messages",
            {
                "$top": 50,
                "$orderby": "lastModifiedDateTime desc",
                "$filter": "lastModifiedDateTime gt 2026-03-05T09:30:00.12Z",
            },
            PREFER,
        )
    ]


def test_a_message_returned_twice_is_kept_once_in_its_latest_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    newer, other, older = {"id": "m1", "v": 2}, {"id": "m2"}, {"id": "m1", "v": 1}
    monkeypatch.setattr(
        api, "get_all_pages", lambda *args: graph.Pages([newer, other, older], None)
    )

    messages = api.list_messages(object(), "c1", "2026-01-01T00:00:00Z")  # type: ignore[arg-type]

    assert messages == [newer, other]


def test_chats_are_listed_by_last_message_and_paged_only_as_consumed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    made: list[tuple[str, Any, Any]] = []
    pages_fetched: list[int] = []

    def fake_iter_pages(session: object, url: str, params: Any, headers: Any) -> Iterator[Any]:
        made.append((url, params, headers))
        for number in range(3):
            pages_fetched.append(number)
            yield {"value": [{"id": f"c{number}a"}, {"id": f"c{number}b"}]}

    monkeypatch.setattr(api, "iter_pages", fake_iter_pages)

    chats = list(islice(api.iter_chats_by_last_message(object()), 2))  # type: ignore[arg-type]

    assert [chat["id"] for chat in chats] == ["c0a", "c0b"]
    assert pages_fetched == [0]
    assert made == [
        (
            f"{graph.GRAPH_URL}/me/chats",
            {
                "$top": 50,
                "$expand": "members,lastMessagePreview",
                "$orderby": "lastMessagePreview/createdDateTime desc",
            },
            PREFER,
        )
    ]


def test_my_user_id_comes_from_me(monkeypatch: pytest.MonkeyPatch) -> None:
    made: list[tuple[str, Any]] = []

    def fake_get_json(session: object, url: str, params: Any) -> dict[str, str]:
        made.append((url, params))
        return {"id": "user-me"}

    monkeypatch.setattr(api, "get_json", fake_get_json)

    assert api.my_user_id(object()) == "user-me"  # type: ignore[arg-type]
    assert made == [(f"{graph.GRAPH_URL}/me", {"$select": "id"})]

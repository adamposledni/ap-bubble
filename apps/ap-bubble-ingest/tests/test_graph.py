import json
from typing import Any

import pytest
import requests

from bubble_ingest.l0_sync import CursorExpired
from bubble_ingest.microsoft import graph


def _response(status: int, body: dict[str, Any], headers: dict[str, str] | None = None):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(body).encode()
    response.headers.update(headers or {})
    response.url = "https://graph.example/test"
    return response


class FakeSession:
    """Answers GETs from a script and records (url, params) requests."""

    def __init__(self, *responses: requests.Response) -> None:
        self.responses = list(responses)
        self.requests: list[tuple[str, Any]] = []

    def get(self, url: str, params: Any = None, **_: Any) -> requests.Response:
        self.requests.append((url, params))
        return self.responses.pop(0)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    slept: list[float] = []
    monkeypatch.setattr(graph.time, "sleep", slept.append)
    return slept


def test_pages_are_followed_and_the_delta_link_kept() -> None:
    session = FakeSession(
        _response(200, {"value": [{"id": 1}], "@odata.nextLink": "https://next"}),
        _response(200, {"value": [{"id": 2}], "@odata.deltaLink": "https://delta"}),
    )

    pages = graph.get_all_pages(session, "https://start", {"$top": 1})  # type: ignore[arg-type]

    assert (pages.items, pages.delta_link) == ([{"id": 1}, {"id": 2}], "https://delta")
    assert session.requests == [("https://start", {"$top": 1}), ("https://next", None)]


def test_throttled_call_waits_for_retry_after(no_sleep: list[float]) -> None:
    session = FakeSession(
        _response(429, {}, {"Retry-After": "7"}),
        _response(200, {"value": []}),
    )

    graph.get_json(session, "https://start")  # type: ignore[arg-type]

    assert no_sleep == [7.0]


def test_expired_delta_link_raises_cursor_expired() -> None:
    session = FakeSession(_response(410, {"error": {"code": "syncStateNotFound"}}))

    with pytest.raises(CursorExpired):
        graph.get_delta(session, "https://start", None, "https://old-delta")  # type: ignore[arg-type]


def test_delta_without_link_starts_from_the_url() -> None:
    session = FakeSession(_response(200, {"value": [], "@odata.deltaLink": "https://delta"}))

    pages = graph.get_delta(session, "https://start", {"a": "b"}, None)  # type: ignore[arg-type]

    assert pages.delta_link == "https://delta"
    assert session.requests == [("https://start", {"a": "b"})]

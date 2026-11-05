import json
from typing import Any

import pytest
import requests

from bubble_ingest.google.gmail import api, retry
from bubble_ingest.l0_sync import CursorExpired

RATE_LIMITED = {"error": {"code": 403, "errors": [{"reason": "rateLimitExceeded"}]}}
NO_PERMISSION = {"error": {"code": 403, "errors": [{"reason": "insufficientPermissions"}]}}


def _response(status: int, body: dict[str, Any]) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(body).encode()
    response.url = "https://gmail.googleapis.com/test"
    return response


class FakeSession:
    """Answers GETs with scripted responses and records (url, params) of each."""

    def __init__(self, *responses: requests.Response) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, params: dict[str, Any] | None = None, timeout: float = 0) -> Any:
        self.calls.append((url, dict(params or {})))
        return self.responses.pop(0)


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    slept: list[float] = []
    monkeypatch.setattr(retry.time, "sleep", slept.append)
    return slept


def test_get_message_asks_for_the_full_format() -> None:
    session = FakeSession(_response(200, {"id": "m1"}))

    assert api.get_message(session, "m1") == {"id": "m1"}
    assert session.calls == [(f"{api.BASE_URL}/messages/m1", {"format": "full"})]


def test_get_message_of_a_deleted_message_is_none() -> None:
    session = FakeSession(_response(404, {"error": {"code": 404}}))

    assert api.get_message(session, "m1") is None


def test_list_history_follows_pages_and_returns_the_last_history_id() -> None:
    session = FakeSession(
        _response(200, {"history": [{"id": "1"}], "nextPageToken": "p2", "historyId": "5"}),
        _response(200, {"history": [{"id": "2"}], "historyId": "7"}),
    )

    history = api.list_history(session, "100")

    assert (history.records, history.history_id) == ([{"id": "1"}, {"id": "2"}], "7")
    params = session.calls[0][1]
    assert params["startHistoryId"] == "100"
    assert params["historyTypes"] == [
        "messageAdded",
        "messageDeleted",
        "labelAdded",
        "labelRemoved",
    ]
    assert session.calls[1][1]["pageToken"] == "p2"


def test_list_history_with_an_expired_start_raises_cursor_expired() -> None:
    session = FakeSession(_response(404, {"error": {"code": 404}}))

    with pytest.raises(CursorExpired):
        api.list_history(session, "100")


def test_list_message_ids_leaves_out_spam_and_trash() -> None:
    session = FakeSession(_response(200, {"messages": [{"id": "m1", "threadId": "t1"}]}))

    assert api.list_message_ids(session, "after:1") == ["m1"]
    assert session.calls[0][1]["includeSpamTrash"] == "false"


@pytest.mark.parametrize(
    "failure",
    [_response(403, RATE_LIMITED), _response(429, {}), _response(503, {})],
    ids=["rate-limited", "too-many-requests", "server-error"],
)
def test_transient_failures_are_retried_after_a_wait(
    failure: requests.Response, sleeps: list[float]
) -> None:
    session = FakeSession(failure, _response(200, {"historyId": "9"}))

    assert api.current_history_id(session) == "9"
    assert len(sleeps) == 1


def test_other_errors_are_not_retried(sleeps: list[float]) -> None:
    session = FakeSession(_response(403, NO_PERMISSION))

    with pytest.raises(requests.HTTPError):
        api.current_history_id(session)
    assert sleeps == []


def test_retries_give_up_after_max_attempts(sleeps: list[float]) -> None:
    session = FakeSession(*[_response(429, {}) for _ in range(retry.MAX_ATTEMPTS)])

    with pytest.raises(requests.HTTPError):
        api.current_history_id(session)
    assert len(session.calls) == retry.MAX_ATTEMPTS
    assert len(sleeps) == retry.MAX_ATTEMPTS - 1
    assert max(sleeps) < 33


def test_connection_errors_are_retried(sleeps: list[float]) -> None:
    calls = iter([requests.ConnectionError("reset"), "ok"])

    def call() -> str:
        result = next(calls)
        if isinstance(result, Exception):
            raise result
        return result

    assert retry.with_retry(call) == "ok"
    assert len(sleeps) == 1

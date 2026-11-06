import json
from typing import Any

import pytest
import requests

from bubble_ingest.l0_sync import CursorExpired
from bubble_ingest.microsoft.mail import api
from bubble_ingest.microsoft.mail.scope import RECEIVED_FILTER

DELTA_URL = f"{api.FOLDERS_URL}/f1/messages/delta"


def _response(status: int, body: dict[str, Any]) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(body).encode()
    response.url = "https://graph.example/test"
    return response


class FakeSession:
    """Answers GETs from a script and records (url, params, headers) requests."""

    def __init__(self, *responses: requests.Response) -> None:
        self.responses = list(responses)
        self.requests: list[tuple[str, Any, Any]] = []

    def get(self, url: str, params: Any = None, headers: Any = None, **_: Any) -> requests.Response:
        self.requests.append((url, params, headers))
        return self.responses.pop(0)


def _pages(session: FakeSession, delta_link: str | None, received_filter: str | None) -> list:
    return list(api.iter_message_pages(session, "f1", delta_link, received_filter))  # type: ignore[arg-type]


def test_first_load_selects_filters_and_sends_the_preferences_on_every_page() -> None:
    session = FakeSession(
        _response(200, {"value": [{"id": "m1"}], "@odata.nextLink": "https://next"}),
        _response(200, {"value": [{"id": "m2"}], "@odata.deltaLink": "https://delta"}),
    )

    pages = _pages(session, None, RECEIVED_FILTER)

    assert [(p.entries, p.delta_link) for p in pages] == [
        ([{"id": "m1"}], None),
        ([{"id": "m2"}], "https://delta"),
    ]
    (first_url, params, headers), (next_url, next_params, next_headers) = session.requests
    assert (first_url, next_url, next_params) == (DELTA_URL, "https://next", None)
    assert params["$filter"] == "receivedDateTime ge 2026-01-01T00:00:00Z"
    assert {"subject", "body", "conversationId", "parentFolderId"} <= set(
        params["$select"].split(",")
    )
    prefer = headers["Prefer"]
    assert 'outlook.body-content-type="text"' in prefer
    assert 'IdType="ImmutableId"' in prefer
    assert "odata.maxpagesize=100" in prefer
    assert next_headers == headers


def test_unfiltered_first_load_has_no_filter() -> None:
    session = FakeSession(_response(200, {"value": [], "@odata.deltaLink": "https://delta"}))

    _pages(session, None, None)

    assert "$filter" not in session.requests[0][1]


def test_delta_link_is_followed_as_it_is() -> None:
    session = FakeSession(_response(200, {"value": [], "@odata.deltaLink": "https://delta-2"}))

    pages = _pages(session, "https://delta-1", None)

    assert pages[0].delta_link == "https://delta-2"
    assert session.requests[0][:2] == ("https://delta-1", None)


@pytest.mark.parametrize(
    ("status", "body"),
    [(410, {}), (400, {"error": {"code": "SyncStateNotFound"}})],
)
def test_expired_delta_link_raises_cursor_expired(status: int, body: dict[str, Any]) -> None:
    session = FakeSession(_response(status, body))

    with pytest.raises(CursorExpired):
        _pages(session, "https://old-delta", None)


def test_other_errors_are_raised_as_they_are() -> None:
    session = FakeSession(_response(400, {"error": {"code": "BadRequest"}}))

    with pytest.raises(requests.HTTPError):
        _pages(session, "https://delta", None)


def test_well_known_folder_id_is_none_when_the_mailbox_has_no_such_folder() -> None:
    session = FakeSession(
        _response(200, {"id": "deleted-id"}),
        _response(404, {"error": {"code": "ErrorFolderNotFound"}}),
    )

    assert api.well_known_folder_id(session, "deleteditems") == "deleted-id"  # type: ignore[arg-type]
    assert api.well_known_folder_id(session, "conversationhistory") is None  # type: ignore[arg-type]
    assert session.requests[0][0] == f"{api.FOLDERS_URL}/deleteditems"


def test_folders_are_listed_from_the_top_or_below_a_parent() -> None:
    session = FakeSession(
        _response(200, {"value": [{"id": "inbox"}]}),
        _response(200, {"value": [{"id": "sub"}]}),
    )

    assert api.list_folders(session, None) == [{"id": "inbox"}]  # type: ignore[arg-type]
    assert api.list_folders(session, "inbox") == [{"id": "sub"}]  # type: ignore[arg-type]
    urls = [url for url, _, _ in session.requests]
    assert urls == [api.FOLDERS_URL, f"{api.FOLDERS_URL}/inbox/childFolders"]

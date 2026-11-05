import json
from typing import Any

import pytest
import requests

from bubble_ingest.google.contacts import api
from bubble_ingest.l0_sync import CursorExpired


class FakeSession:
    """Answers GETs with scripted responses and records (url, params) of each request."""

    def __init__(self, *responses: requests.Response) -> None:
        self.responses = list(responses)
        self.requests: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, params: dict[str, Any], timeout: float) -> requests.Response:
        self.requests.append((url, dict(params)))
        return self.responses.pop(0)


def _response(status: int, body: dict[str, Any]) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(body).encode()
    response.url = api.BASE_URL
    return response


def _expired_error() -> dict[str, Any]:
    info = {"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": "EXPIRED_SYNC_TOKEN"}
    return {"error": {"code": 400, "status": "FAILED_PRECONDITION", "details": [info]}}


def test_full_load_requests_a_sync_token_and_follows_pages() -> None:
    session = FakeSession(
        _response(200, {"connections": [{"resourceName": "people/c1"}], "nextPageToken": "p2"}),
        _response(200, {"connections": [{"resourceName": "people/c2"}], "nextSyncToken": "s1"}),
    )

    changes = api.list_people(session, api.CONNECTIONS, None)

    assert [p["resourceName"] for p in changes.people] == ["people/c1", "people/c2"]
    assert changes.next_sync_token == "s1"
    url, params = session.requests[0]
    assert url == f"{api.BASE_URL}/people/me/connections"
    assert params == {
        "personFields": api.CONNECTIONS.mask,
        "pageSize": 1000,
        "requestSyncToken": "true",
    }
    assert session.requests[1][1]["pageToken"] == "p2"


def test_incremental_fetch_repeats_the_parameters_of_the_full_load() -> None:
    session = FakeSession(_response(200, {"nextSyncToken": "s2"}))

    changes = api.list_people(session, api.OTHER_CONTACTS, "s1")

    assert changes == api.PeopleChanges([], "s2")
    assert session.requests == [
        (
            f"{api.BASE_URL}/otherContacts",
            {
                "readMask": "emailAddresses,metadata,names,phoneNumbers,photos",
                "pageSize": 1000,
                "requestSyncToken": "true",
                "syncToken": "s1",
            },
        )
    ]


@pytest.mark.parametrize(
    ("status", "body"), [(410, {}), (400, _expired_error())], ids=["gone", "expired-reason"]
)
def test_expired_sync_token_raises_cursor_expired(status: int, body: dict[str, Any]) -> None:
    session = FakeSession(_response(status, body))

    with pytest.raises(CursorExpired):
        api.list_people(session, api.CONNECTIONS, "old")


def test_other_bad_request_is_raised_as_is() -> None:
    session = FakeSession(_response(400, {"error": {"status": "INVALID_ARGUMENT"}}))

    with pytest.raises(requests.HTTPError):
        api.list_people(session, api.CONNECTIONS, "old")

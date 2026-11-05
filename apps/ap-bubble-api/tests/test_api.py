from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from bubble_api.app import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """The API on a fresh vault in the test's data folder (see apps/conftest.py)."""
    with TestClient(create_app()) as client:
        yield client


def test_agenda_and_tasks_of_an_empty_vault(client: TestClient) -> None:
    agenda = client.get("/api/agenda", params={"start": "2026-11-05", "tz": "Europe/Prague"})

    assert (agenda.status_code, agenda.json()) == (200, [])
    assert client.get("/api/tasks").json() == []


def test_unknown_time_zone_is_rejected(client: TestClient) -> None:
    response = client.get("/api/agenda", params={"start": "2026-11-05", "tz": "Mars/Base"})

    assert response.status_code == 422


def test_input_with_text_and_file_is_queued_and_downloadable(client: TestClient) -> None:
    response = client.post(
        "/api/inputs",
        data={"text": "Contract for the flat"},
        files=[("files", ("contract.txt", b"signed", "text/plain"))],
    )

    assert response.status_code == 201
    created = response.json()
    assert (created["text"], created["status"]) == ("Contract for the flat", "queued")
    [file] = created["files"]
    assert (file["name"], file["sizeBytes"]) == ("contract.txt", 6)
    assert client.get(f"/api/inputs/files/{file['id']}").content == b"signed"
    assert [item["id"] for item in client.get("/api/inputs").json()] == [created["id"]]


def test_empty_input_is_rejected(client: TestClient) -> None:
    assert client.post("/api/inputs", data={"text": " "}).status_code == 422


def test_queued_input_is_deleted(client: TestClient) -> None:
    created = client.post("/api/inputs", data={"text": "oops"}).json()

    assert client.delete(f"/api/inputs/{created['id']}").status_code == 204
    assert client.get("/api/inputs").json() == []
    assert client.delete(f"/api/inputs/{created['id']}").status_code == 404

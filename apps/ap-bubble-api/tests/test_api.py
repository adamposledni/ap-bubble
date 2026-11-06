from collections.abc import Iterator
from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from bubble_api.app import create_app
from bubble_core.db import open_vault
from bubble_core.input_queue import set_status
from bubble_core.paths import curator_runs_dir, knowledge_dir


@pytest.fixture
def client() -> Iterator[TestClient]:
    """The API on a fresh vault in the test's data folder (see apps/conftest.py)."""
    with TestClient(create_app()) as client:
        yield client


def test_agenda_and_tasks_of_an_empty_vault(client: TestClient) -> None:
    agenda = client.get("/api/agenda", params={"start": "2026-11-05", "tz": "Europe/Prague"})

    assert (agenda.status_code, agenda.json()) == (200, [])
    assert client.get("/api/tasks").json() == []


def test_monitor_of_an_empty_vault(client: TestClient) -> None:
    response = client.get("/api/monitor")

    assert (response.status_code, response.json()) == (
        200,
        {"jobs": [], "runs": [], "running": [], "queue": {}},
    )


def test_unknown_run_and_unsafe_batch_names_are_not_found(client: TestClient) -> None:
    assert client.get("/api/monitor/runs/999").status_code == 404
    assert client.get("/api/monitor/runs/1/batches/knowledge-index.md").status_code == 404
    assert client.get("/api/monitor/runs/1/batches/batch-01.md").status_code == 404


def test_batch_file_is_served_as_text(client: TestClient) -> None:
    batch = curator_runs_dir() / "1" / "batch-01.md"
    batch.parent.mkdir(parents=True)
    batch.write_text("# batch", encoding="utf-8")

    response = client.get("/api/monitor/runs/1/batches/batch-01.md")

    assert (response.status_code, response.text) == (200, "# batch")


def test_monitor_counts_the_queue(client: TestClient) -> None:
    client.post("/api/inputs", data={"text": "note"})

    assert client.get("/api/monitor").json()["queue"] == {"queued": 1}


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


def test_done_inputs_can_be_left_out(client: TestClient) -> None:
    done = client.post("/api/inputs", data={"text": "old"}).json()
    open_ = client.post("/api/inputs", data={"text": "new"}).json()
    with closing(open_vault()) as conn:
        set_status(conn, [done["id"]], "done")

    listed = client.get("/api/inputs", params={"include_done": False}).json()

    assert [item["id"] for item in listed] == [open_["id"]]
    assert len(client.get("/api/inputs").json()) == 2


def _write_questions(text: str) -> None:
    (knowledge_dir() / "questions.md").write_text(text, encoding="utf-8")


def test_questions_are_listed(client: TestClient) -> None:
    assert client.get("/api/questions").json() == []
    _write_questions("# Open questions\n\n- Which Petr?\n")

    [question] = client.get("/api/questions").json()

    assert question["text"] == "Which Petr?"


def test_answering_a_question_queues_an_input_and_removes_it(client: TestClient) -> None:
    _write_questions("# Open questions\n\n- Which Petr?\n")
    [question] = client.get("/api/questions").json()

    response = client.post(f"/api/questions/{question['id']}/answer", json={"text": "Novak"})

    assert response.status_code == 201
    assert response.json()["text"] == 'Answer to the curator\'s question "Which Petr?":\n\nNovak'
    assert client.get("/api/questions").json() == []
    assert len(client.get("/api/inputs").json()) == 1


def test_dismissing_a_question_removes_it(client: TestClient) -> None:
    _write_questions("- Which Petr?\n")
    [question] = client.get("/api/questions").json()

    assert client.post(f"/api/questions/{question['id']}/dismiss").status_code == 204
    assert client.get("/api/questions").json() == []
    assert client.get("/api/inputs").json() == []


def test_unknown_question_is_not_found(client: TestClient) -> None:
    assert client.post("/api/questions/nope/dismiss").status_code == 404
    assert client.post("/api/questions/nope/answer", json={"text": "x"}).status_code == 404


def test_knowledge_search_and_doc(client: TestClient) -> None:
    people = knowledge_dir() / "people"
    people.mkdir(parents=True)
    (people / "petr-novak.md").write_text("---\nname: Petr Novák\n---\nColleague.", "utf-8")
    (people / "jana.md").write_text("---\nname: Jana\n---\nKnows [Petr](petr-novak.md).", "utf-8")

    found = client.get("/api/knowledge", params={"q": "novak", "folder": "people"}).json()
    doc = client.get("/api/knowledge/people/petr-novak").json()

    assert (found["total"], found["hits"][0]["slug"]) == (1, "petr-novak")
    assert (doc["meta"]["name"], doc["body"]) == ("Petr Novák", "Colleague.")
    assert doc["backlinks"] == [{"folder": "people", "slug": "jana", "name": "Jana"}]


def test_knowledge_search_takes_query_syntax_as_text(client: TestClient) -> None:
    response = client.get("/api/knowledge", params={"q": 'NOT "petr (* ^'})

    assert (response.status_code, response.json()) == (200, {"total": 0, "hits": []})


def test_unknown_knowledge_doc_is_not_found(client: TestClient) -> None:
    assert client.get("/api/knowledge/people/missing").status_code == 404
    assert client.get("/api/knowledge/people/..%5Cvault").status_code == 404
    assert client.get("/api/knowledge/secrets/x").status_code == 422

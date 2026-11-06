import sqlite3
from collections.abc import Iterator
from datetime import datetime
from typing import Any

import pytest
import requests

from bubble_core.accounts import Account, upsert_account
from bubble_core.sync_cursors import load_cursor
from bubble_ingest.microsoft import auth as microsoft_auth
from bubble_ingest.microsoft.chats import api
from bubble_ingest.microsoft.chats.sync import SYNC_FROM, sync_account


class FakeTeams:
    """Chats sorted by last message and their messages; honours the lastModifiedDateTime filter.

    Records how many chats were listed and each (chat_id, modified_after) messages request.
    Chats in `failing` answer their messages request with that HTTP status.
    """

    def __init__(self) -> None:
        self.chats: list[dict[str, Any]] = []
        self.messages: dict[str, list[dict[str, Any]]] = {}
        self.failing: dict[str, int] = {}
        self.chats_listed = 0
        self.requests: list[tuple[str, str]] = []

    def iter_chats(self, session: object) -> Iterator[dict[str, Any]]:
        for chat in self.chats:
            self.chats_listed += 1
            yield chat

    def list_messages(
        self, session: object, chat_id: str, modified_after: str
    ) -> list[dict[str, Any]]:
        self.requests.append((chat_id, modified_after))
        if chat_id in self.failing:
            response = requests.Response()
            response.status_code = self.failing[chat_id]
            raise requests.HTTPError(f"{response.status_code} error", response=response)
        after = datetime.fromisoformat(modified_after)
        messages = self.messages.get(chat_id, [])
        return [m for m in messages if datetime.fromisoformat(m["lastModifiedDateTime"]) > after]

    def add_chat(self, chat_id: str, last_message_at: str | None, topic: str = "Chat") -> None:
        preview = {"id": "p", "createdDateTime": last_message_at} if last_message_at else None
        chat = {"id": chat_id, "topic": topic, "members": [], "lastMessagePreview": preview}
        self.chats.append(chat)

    def post(self, chat_id: str, message_id: str, at: str, text: str = "hi") -> None:
        """A new message at the given time, also as the chat's last message."""
        self.messages.setdefault(chat_id, []).append(_message(message_id, at, text=text))
        self._chat(chat_id)["lastMessagePreview"] = {"id": message_id, "createdDateTime": at}

    def change(self, chat_id: str, message_id: str, at: str, **fields: Any) -> None:
        """Edit, react to or delete a message: lastModifiedDateTime moves, the preview does not."""
        message = next(m for m in self.messages[chat_id] if m["id"] == message_id)
        message.update(lastModifiedDateTime=at, **fields)

    def _chat(self, chat_id: str) -> dict[str, Any]:
        return next(chat for chat in self.chats if chat["id"] == chat_id)


def _message(message_id: str, created: str, text: str = "hi") -> dict[str, Any]:
    return {
        "id": message_id,
        "messageType": "message",
        "createdDateTime": created,
        "lastModifiedDateTime": created,
        "deletedDateTime": None,
        "body": {"contentType": "text", "content": text},
    }


@pytest.fixture
def work(conn: sqlite3.Connection) -> Account:
    return upsert_account(conn, "microsoft", "me@work.example", "work")


@pytest.fixture
def teams(monkeypatch: pytest.MonkeyPatch) -> FakeTeams:
    fake = FakeTeams()
    monkeypatch.setattr(microsoft_auth, "session_for", lambda account_key: object())
    monkeypatch.setattr(api, "my_user_id", lambda session: "user-me")
    monkeypatch.setattr(api, "iter_chats_by_last_message", fake.iter_chats)
    monkeypatch.setattr(api, "list_messages", fake.list_messages)
    return fake


def _messages(conn: sqlite3.Connection) -> dict[str, tuple[int, str | None]]:
    rows = conn.execute(
        "SELECT external_id, deleted, title FROM l0_items WHERE kind = 'chat_message'"
    ).fetchall()
    return {row["external_id"]: (row["deleted"], row["title"]) for row in rows}


def _chats(conn: sqlite3.Connection) -> dict[str, str | None]:
    rows = conn.execute("SELECT external_id, title FROM l0_items WHERE kind = 'chat'").fetchall()
    return {row["external_id"]: row["title"] for row in rows}


def _cursor(conn: sqlite3.Connection, account: Account, chat_id: str) -> str | None:
    return load_cursor(conn, account.id, "teams_chats", chat_id)


def test_first_sync_loads_each_active_chat_since_sync_from(
    conn: sqlite3.Connection, work: Account, teams: FakeTeams
) -> None:
    teams.add_chat("c1", None, topic="Project X")
    teams.post("c1", "m1", "2026-03-01T10:00:00Z", text="Hello")
    teams.add_chat("c2", None)
    teams.post("c2", "m2", "2026-02-01T10:00:00Z")

    sync_account(conn, work)

    assert teams.requests == [("c1", SYNC_FROM), ("c2", SYNC_FROM)]
    assert _messages(conn) == {"m1": (0, "Hello"), "m2": (0, "hi")}
    assert _chats(conn) == {"c1": "Project X", "c2": "Chat"}
    assert _cursor(conn, work, "c1") == "2026-03-01T10:00:00Z"


def test_listing_stops_at_the_first_chat_older_than_sync_from(
    conn: sqlite3.Connection, work: Account, teams: FakeTeams
) -> None:
    teams.add_chat("active", "2026-03-01T10:00:00Z")
    teams.add_chat("empty", None)
    teams.add_chat("old", "2025-12-31T23:59:59Z")
    teams.add_chat("older", "2025-06-01T10:00:00Z")

    sync_account(conn, work)

    assert teams.chats_listed == 3
    assert set(_chats(conn)) == {"active"}
    assert [chat_id for chat_id, _ in teams.requests] == ["active"]


def test_chat_without_a_new_message_is_skipped(
    conn: sqlite3.Connection, work: Account, teams: FakeTeams
) -> None:
    teams.add_chat("c1", None)
    teams.post("c1", "m1", "2026-03-01T10:00:00Z")
    sync_account(conn, work)
    teams.requests.clear()

    sync_account(conn, work)

    assert teams.requests == []


def test_new_message_is_fetched_since_the_cursor(
    conn: sqlite3.Connection, work: Account, teams: FakeTeams
) -> None:
    teams.add_chat("c1", None)
    teams.post("c1", "m1", "2026-03-01T10:00:00Z")
    sync_account(conn, work)
    teams.post("c1", "m2", "2026-03-02T08:00:00.25Z")

    sync_account(conn, work)

    assert teams.requests[-1] == ("c1", "2026-03-01T10:00:00Z")
    assert set(_messages(conn)) == {"m1", "m2"}
    assert _cursor(conn, work, "c1") == "2026-03-02T08:00:00.25Z"


def test_cursor_is_the_latest_modification_by_time_not_by_text(
    conn: sqlite3.Connection, work: Account, teams: FakeTeams
) -> None:
    teams.add_chat("c1", None)
    teams.post("c1", "m1", "2026-03-01T10:00:00.4Z")
    teams.post("c1", "m2", "2026-03-01T10:00:00.45Z")
    teams.change("c1", "m1", "2026-03-01T10:00:00.5Z")
    teams.change("c1", "m2", "2026-03-01T10:00:00.55Z")  # as text, '.5Z' sorts after '.55Z'

    sync_account(conn, work)

    assert _cursor(conn, work, "c1") == "2026-03-01T10:00:00.55Z"


def test_edits_and_deletions_arrive_with_the_next_new_message(
    conn: sqlite3.Connection, work: Account, teams: FakeTeams
) -> None:
    teams.add_chat("c1", None)
    teams.post("c1", "m1", "2026-03-01T10:00:00Z", text="Draft")
    teams.post("c1", "m2", "2026-03-01T11:00:00Z", text="Oops")
    sync_account(conn, work)
    teams.change(
        "c1", "m1", "2026-03-02T09:00:00Z", body={"contentType": "text", "content": "Fixed"}
    )
    teams.change("c1", "m2", "2026-03-02T09:05:00Z", deletedDateTime="2026-03-02T09:05:00Z")
    sync_account(conn, work)
    assert _messages(conn) == {"m1": (0, "Draft"), "m2": (0, "Oops")}  # last message unchanged

    teams.post("c1", "m3", "2026-03-02T10:00:00Z")
    sync_account(conn, work)

    assert _messages(conn) == {"m1": (0, "Fixed"), "m2": (1, "Oops"), "m3": (0, "hi")}


def test_messages_created_before_sync_from_are_not_kept(
    conn: sqlite3.Connection, work: Account, teams: FakeTeams
) -> None:
    teams.add_chat("c1", None)
    teams.post("c1", "old", "2025-12-30T10:00:00Z")
    teams.change("c1", "old", "2026-01-05T10:00:00Z")  # e.g. a late reaction
    teams.post("c1", "new", "2026-01-06T10:00:00Z")

    sync_account(conn, work)

    assert set(_messages(conn)) == {"new"}


def test_cursor_reaches_the_last_message_even_when_the_list_lacks_it(
    conn: sqlite3.Connection, work: Account, teams: FakeTeams
) -> None:
    teams.add_chat("c1", "2026-03-01T10:00:00Z")  # no message is listed
    sync_account(conn, work)
    teams.requests.clear()

    sync_account(conn, work)

    assert _cursor(conn, work, "c1") == "2026-03-01T10:00:00Z"
    assert teams.requests == []


def test_chat_with_forbidden_messages_is_skipped_until_its_next_message(
    conn: sqlite3.Connection, work: Account, teams: FakeTeams
) -> None:
    teams.add_chat("forbidden", "2026-03-02T10:00:00Z")
    teams.failing["forbidden"] = 403
    teams.add_chat("c1", None)
    teams.post("c1", "m1", "2026-03-01T10:00:00Z")

    sync_account(conn, work)
    teams.requests.clear()
    sync_account(conn, work)

    assert set(_messages(conn)) == {"m1"}
    assert set(_chats(conn)) == {"forbidden", "c1"}
    assert _cursor(conn, work, "forbidden") == "2026-03-02T10:00:00Z"
    assert teams.requests == []


def test_other_failures_fail_the_run(
    conn: sqlite3.Connection, work: Account, teams: FakeTeams
) -> None:
    teams.add_chat("c1", None)
    teams.post("c1", "m1", "2026-03-01T10:00:00Z")
    teams.failing["c1"] = 500

    with pytest.raises(requests.HTTPError):
        sync_account(conn, work)

    assert _cursor(conn, work, "c1") is None
    (status,) = conn.execute("SELECT status FROM lm_job_runs").fetchone()
    assert status == "failed"


def test_full_load_after_dropping_cursors_flags_messages_gone_from_graph(
    conn: sqlite3.Connection, work: Account, teams: FakeTeams
) -> None:
    teams.add_chat("c1", None)
    teams.post("c1", "m1", "2026-03-01T10:00:00Z")
    teams.post("c1", "m2", "2026-03-01T11:00:00Z")
    sync_account(conn, work)
    teams.messages["c1"].pop(0)  # e.g. removed by a retention policy
    conn.execute("DELETE FROM lm_sync_cursors")

    sync_account(conn, work)

    assert _messages(conn) == {"m1": (1, "hi"), "m2": (0, "hi")}


def test_sync_is_recorded_as_job_run(
    conn: sqlite3.Connection, work: Account, teams: FakeTeams
) -> None:
    teams.add_chat("c1", None)
    teams.post("c1", "m1", "2026-03-01T10:00:00Z")
    teams.post("c1", "m2", "2026-03-01T11:00:00Z")

    sync_account(conn, work)

    row = conn.execute("SELECT * FROM lm_job_runs").fetchone()
    assert (row["job_name"], row["scope"], row["status"], row["items_processed"]) == (
        "ingest.teams_chats",
        "microsoft:me@work.example",
        "succeeded",
        2,
    )

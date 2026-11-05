import json
import sqlite3
from typing import Any

import pytest
import requests

from bubble_core.accounts import Account
from bubble_core.sync_cursors import load_cursor
from bubble_ingest.google import auth as google_auth
from bubble_ingest.google.gmail import api, store
from bubble_ingest.google.gmail.sync import sync_account
from bubble_ingest.l0_sync import CursorExpired

RECENT_MS = "1772705400000"  # 2026-03-05, after SYNC_FROM
OLD_MS = "1735689600000"  # 2025-01-01, before SYNC_FROM


class FakeGmail:
    """A scripted mailbox; records each request ('profile', 'list', 'history:<id>', 'get:<id>')."""

    def __init__(self) -> None:
        self.messages: dict[str, dict[str, Any]] = {}
        self.history: list[dict[str, Any]] = []
        self.history_id = "100"
        self.history_expired = False
        self.broken_id: str | None = None
        self.requests: list[str] = []

    def current_history_id(self, session: object) -> str:
        self.requests.append("profile")
        return self.history_id

    def list_message_ids(self, session: object, query: str) -> list[str]:
        self.requests.append("list")
        excluded = {"SPAM", "TRASH"}
        return [i for i, m in self.messages.items() if not excluded & set(m["labelIds"])]

    def list_history(self, session: object, start_history_id: str) -> api.History:
        self.requests.append(f"history:{start_history_id}")
        if self.history_expired:
            raise CursorExpired(start_history_id)
        return api.History(list(self.history), self.history_id)

    def get_message(self, session: object, message_id: str) -> dict[str, Any] | None:
        self.requests.append(f"get:{message_id}")
        if message_id == self.broken_id:
            raise requests.ConnectionError("network down")
        return self.messages.get(message_id)

    def add(self, message_id: str, *labels: str, internal_date: str = RECENT_MS) -> None:
        self.messages[message_id] = {
            "id": message_id,
            "threadId": message_id,
            "labelIds": list(labels or ["INBOX"]),
            "internalDate": internal_date,
            "payload": {"headers": [{"name": "Subject", "value": f"About {message_id}"}]},
        }

    def record(self, kind: str, message_id: str) -> None:
        self.history.append({"id": "1", kind: [{"message": {"id": message_id}}]})


@pytest.fixture
def gmail(monkeypatch: pytest.MonkeyPatch) -> FakeGmail:
    fake = FakeGmail()
    monkeypatch.setattr(google_auth, "session_for", lambda account_key: object())
    for name in ("current_history_id", "list_message_ids", "list_history", "get_message"):
        monkeypatch.setattr(api, name, getattr(fake, name))
    return fake


def _rows(conn: sqlite3.Connection) -> dict[str, tuple[int, str | None]]:
    rows = conn.execute("SELECT external_id, deleted, title FROM l0_items").fetchall()
    return {row["external_id"]: (row["deleted"], row["title"]) for row in rows}


def _labels(conn: sqlite3.Connection, message_id: str) -> list[str]:
    (payload,) = conn.execute(
        "SELECT payload FROM l0_items WHERE external_id = ?", (message_id,)
    ).fetchone()
    return json.loads(payload)["labelIds"]


def _cursor(conn: sqlite3.Connection, account: Account) -> str | None:
    return load_cursor(conn, account.id, "gmail", "")


def _loaded(conn: sqlite3.Connection, account: Account, gmail: FakeGmail, *ids: str) -> None:
    for message_id in ids:
        gmail.add(message_id)
    sync_account(conn, account)
    gmail.requests.clear()


def test_first_sync_loads_the_mailbox_fully(
    conn: sqlite3.Connection, account: Account, gmail: FakeGmail
) -> None:
    gmail.add("m1")
    gmail.add("m2", "INBOX", "UNREAD")
    gmail.add("spam", "SPAM")

    sync_account(conn, account)

    assert gmail.requests == ["profile", "list", "get:m1", "get:m2"]
    assert _rows(conn) == {"m1": (0, "About m1"), "m2": (0, "About m2")}
    assert _cursor(conn, account) == "100"


def test_full_load_commits_per_batch_and_a_rerun_completes_it(
    conn: sqlite3.Connection, account: Account, gmail: FakeGmail, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store, "BATCH_SIZE", 2)
    for message_id in ("m1", "m2", "m3", "m4", "m5"):
        gmail.add(message_id)
    gmail.broken_id = "m4"

    with pytest.raises(requests.ConnectionError):
        sync_account(conn, account)
    assert set(_rows(conn)) == {"m1", "m2"}  # the first batch was committed, the second failed
    assert _cursor(conn, account) is None

    gmail.broken_id = None
    sync_account(conn, account)

    assert set(_rows(conn)) == {"m1", "m2", "m3", "m4", "m5"}
    assert _cursor(conn, account) == "100"
    statuses = [r["status"] for r in conn.execute("SELECT status FROM lm_job_runs ORDER BY id")]
    assert statuses == ["failed", "succeeded"]


def test_incremental_sync_fetches_added_and_relabelled_messages(
    conn: sqlite3.Connection, account: Account, gmail: FakeGmail
) -> None:
    _loaded(conn, account, gmail, "m1", "m2")
    gmail.add("m3")
    gmail.record("messagesAdded", "m3")
    gmail.add("m1", "INBOX", "STARRED")
    gmail.record("labelsAdded", "m1")
    gmail.history_id = "200"

    sync_account(conn, account)

    assert gmail.requests == ["history:100", "get:m3", "get:m1"]
    assert _rows(conn) == {"m1": (0, "About m1"), "m2": (0, "About m2"), "m3": (0, "About m3")}
    assert _labels(conn, "m1") == ["INBOX", "STARRED"]
    assert _cursor(conn, account) == "200"


def test_incremental_sync_flags_messages_gone_from_scope(
    conn: sqlite3.Connection, account: Account, gmail: FakeGmail
) -> None:
    _loaded(conn, account, gmail, "deleted", "trashed", "vanished", "kept")
    del gmail.messages["deleted"]
    gmail.record("messagesDeleted", "deleted")
    gmail.add("trashed", "TRASH")
    gmail.record("labelsAdded", "trashed")
    del gmail.messages["vanished"]  # deleted after the history was read: 404 on fetch
    gmail.record("labelsRemoved", "vanished")
    gmail.record("messagesDeleted", "never-seen")
    gmail.add("old", internal_date=OLD_MS)
    gmail.record("labelsAdded", "old")

    sync_account(conn, account)

    assert gmail.requests == ["history:100", "get:trashed", "get:vanished", "get:old"]
    assert {i: deleted for i, (deleted, _) in _rows(conn).items()} == {
        "deleted": 1,
        "trashed": 1,
        "vanished": 1,
        "kept": 0,
    }
    assert _rows(conn)["trashed"] == (1, "About trashed")  # known content is kept


def test_message_restored_from_trash_is_undeleted(
    conn: sqlite3.Connection, account: Account, gmail: FakeGmail
) -> None:
    _loaded(conn, account, gmail, "m1")
    gmail.add("m1", "TRASH")
    gmail.record("labelsAdded", "m1")
    sync_account(conn, account)
    assert _rows(conn) == {"m1": (1, "About m1")}
    gmail.history.clear()
    gmail.add("m1", "INBOX")
    gmail.record("labelsRemoved", "m1")

    sync_account(conn, account)

    assert _rows(conn) == {"m1": (0, "About m1")}


def test_incremental_sync_without_history_changes_nothing(
    conn: sqlite3.Connection, account: Account, gmail: FakeGmail
) -> None:
    _loaded(conn, account, gmail, "m1")

    sync_account(conn, account)

    assert gmail.requests == ["history:100"]
    (changed_run,) = conn.execute("SELECT changed_run_id FROM l0_items").fetchone()
    assert changed_run == 1


def test_expired_history_falls_back_to_full_load_and_flags_missing_messages(
    conn: sqlite3.Connection, account: Account, gmail: FakeGmail
) -> None:
    _loaded(conn, account, gmail, "m1", "m2")
    del gmail.messages["m2"]
    gmail.history_expired = True
    gmail.history_id = "300"

    sync_account(conn, account)

    assert gmail.requests == ["history:100", "profile", "list", "get:m1"]
    assert _rows(conn) == {"m1": (0, "About m1"), "m2": (1, "About m2")}
    assert _cursor(conn, account) == "300"


def test_sync_is_recorded_as_job_run(
    conn: sqlite3.Connection, account: Account, gmail: FakeGmail
) -> None:
    gmail.add("m1")
    gmail.add("m2")

    sync_account(conn, account)

    row = conn.execute("SELECT * FROM lm_job_runs").fetchone()
    assert (row["job_name"], row["scope"], row["status"], row["items_processed"]) == (
        "ingest.gmail",
        "google:me@gmail.com",
        "succeeded",
        2,
    )

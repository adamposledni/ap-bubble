import json
import sqlite3
from collections.abc import Iterator
from typing import Any

import pytest
import requests

from bubble_core.accounts import Account, upsert_account
from bubble_core.sync_cursors import load_cursor
from bubble_ingest.l0_sync import CursorExpired
from bubble_ingest.microsoft import auth as microsoft_auth
from bubble_ingest.microsoft.mail import api
from bubble_ingest.microsoft.mail.scope import SYNC_FROM
from bubble_ingest.microsoft.mail.sync import sync_account

SOURCE = "outlook_mail"
RECENT = "2026-03-05T10:20:30Z"
OLD = "2025-06-01T08:00:00Z"  # before SYNC_FROM


class FakeMail:
    """A scripted mailbox: folders, their messages, and the changes a delta link returns.

    Records each delta request as (folder_id, delta_link), or 'filtered' / 'unfiltered' for a
    full load.
    """

    def __init__(self) -> None:
        self.folders = ["inbox", "archive"]
        self.messages: dict[str, dict[str, dict[str, Any]]] = {"inbox": {}, "archive": {}}
        self.changes: dict[str, list[dict[str, Any]]] = {}
        self.expired: set[str] = set()
        self.page_size = 100
        self.fail_at_page: int | None = None
        self.pages_served = 0
        self.rounds = 0  # numbers the delta links handed out
        self.requests: list[tuple[str, str]] = []

    def list_folders(self, session: object, parent_id: str | None) -> list[dict[str, Any]]:
        if parent_id:
            return []
        return [{"id": f, "displayName": f.title(), "childFolderCount": 0} for f in self.folders]

    def iter_message_pages(
        self, session: object, folder_id: str, delta_link: str | None, received_filter: str | None
    ) -> Iterator[api.MessagePage]:
        self.rounds += 1
        if delta_link:
            self.requests.append((folder_id, delta_link))
            if folder_id in self.expired:
                raise CursorExpired(folder_id)
            entries = list(self.changes.get(folder_id, []))
        else:
            self.requests.append((folder_id, "filtered" if received_filter else "unfiltered"))
            entries = self._full(folder_id, received_filter)
        yield from self._pages(entries, f"{folder_id}-link-{self.rounds}")

    def add(self, folder_id: str, message_id: str, received: str = RECENT) -> None:
        self.messages[folder_id][message_id] = message(message_id, received)

    def _full(self, folder_id: str, received_filter: str | None) -> list[dict[str, Any]]:
        entries = list(self.messages[folder_id].values())
        if not received_filter:
            return entries
        return [m for m in entries if m["receivedDateTime"] >= SYNC_FROM][: api.FILTER_CAP]

    def _pages(self, entries: list[dict[str, Any]], link: str) -> Iterator[api.MessagePage]:
        for start in range(0, max(len(entries), 1), self.page_size):
            self.pages_served += 1
            if self.pages_served == self.fail_at_page:
                raise requests.ConnectionError("network down")
            last = start + self.page_size >= len(entries)
            yield api.MessagePage(entries[start : start + self.page_size], link if last else None)


def message(message_id: str, received: str = RECENT, **fields: Any) -> dict[str, Any]:
    return {
        "@odata.etag": f'W/"{message_id}"',
        "id": message_id,
        "subject": f"About {message_id}",
        "receivedDateTime": received,
        "isRead": False,
        **fields,
    }


def removed(message_id: str) -> dict[str, Any]:
    return {"id": message_id, "@removed": {"reason": "deleted"}}


@pytest.fixture
def ms_account(conn: sqlite3.Connection) -> Account:
    return upsert_account(conn, "microsoft", "me@work.example", "work")


@pytest.fixture
def mail(monkeypatch: pytest.MonkeyPatch) -> FakeMail:
    fake = FakeMail()
    monkeypatch.setattr(microsoft_auth, "session_for", lambda account_key: object())
    monkeypatch.setattr(api, "well_known_folder_id", lambda session, name: None)
    monkeypatch.setattr(api, "list_folders", fake.list_folders)
    monkeypatch.setattr(api, "iter_message_pages", fake.iter_message_pages)
    return fake


def _rows(conn: sqlite3.Connection) -> dict[tuple[str, str], int]:
    rows = conn.execute(
        "SELECT container_id, external_id, deleted FROM l0_items WHERE kind = 'mail'"
    )
    return {(row["container_id"], row["external_id"]): row["deleted"] for row in rows}


def _payload(conn: sqlite3.Connection, folder_id: str, message_id: str) -> dict[str, Any]:
    (payload,) = conn.execute(
        "SELECT payload FROM l0_items WHERE container_id = ? AND external_id = ?",
        (folder_id, message_id),
    ).fetchone()
    return json.loads(payload)


def _cursor(conn: sqlite3.Connection, account: Account, folder_id: str) -> str | None:
    return load_cursor(conn, account.id, SOURCE, folder_id)


def _loaded(conn: sqlite3.Connection, account: Account, mail: FakeMail) -> None:
    """Inbox m1, m2 and archive m3, loaded; requests cleared."""
    mail.add("inbox", "m1")
    mail.add("inbox", "m2")
    mail.add("archive", "m3")
    sync_account(conn, account)
    mail.requests.clear()


def test_first_sync_loads_every_folder_fully(
    conn: sqlite3.Connection, ms_account: Account, mail: FakeMail
) -> None:
    mail.add("inbox", "m1")
    mail.add("inbox", "old", received=OLD)
    mail.add("archive", "m2")

    sync_account(conn, ms_account)

    assert mail.requests == [("inbox", "filtered"), ("archive", "filtered")]
    assert _rows(conn) == {("inbox", "m1"): 0, ("archive", "m2"): 0}
    assert _cursor(conn, ms_account, "inbox") == "inbox-link-1"
    assert _cursor(conn, ms_account, "archive") == "archive-link-2"
    folders = conn.execute("SELECT external_id, title FROM l0_items WHERE kind = 'mailfolder'")
    assert {(row["external_id"], row["title"]) for row in folders} == {
        ("inbox", "Inbox"),
        ("archive", "Archive"),
    }


def test_incremental_sync_applies_the_changes_since_the_delta_link(
    conn: sqlite3.Connection, ms_account: Account, mail: FakeMail
) -> None:
    _loaded(conn, ms_account, mail)
    mail.changes["inbox"] = [message("m1", isRead=True), message("m4")]

    sync_account(conn, ms_account)

    assert mail.requests == [("inbox", "inbox-link-1"), ("archive", "archive-link-2")]
    assert _rows(conn) == {
        ("inbox", "m1"): 0,
        ("inbox", "m2"): 0,
        ("inbox", "m4"): 0,
        ("archive", "m3"): 0,
    }
    assert _payload(conn, "inbox", "m1")["isRead"] is True
    assert _cursor(conn, ms_account, "inbox") == "inbox-link-3"
    unchanged = conn.execute("SELECT changed_run_id FROM l0_items WHERE external_id = 'm2'")
    assert unchanged.fetchone()["changed_run_id"] == 1


def test_removed_message_only_flags_known_rows(
    conn: sqlite3.Connection, ms_account: Account, mail: FakeMail
) -> None:
    _loaded(conn, ms_account, mail)
    mail.changes["inbox"] = [removed("m1"), removed("never-seen")]

    sync_account(conn, ms_account)

    assert _rows(conn) == {("inbox", "m1"): 1, ("inbox", "m2"): 0, ("archive", "m3"): 0}
    assert _payload(conn, "inbox", "m1")["subject"] == "About m1"  # known content is kept


def test_moves_between_folders_leave_one_live_row_in_either_order(
    conn: sqlite3.Connection, ms_account: Account, mail: FakeMail
) -> None:
    _loaded(conn, ms_account, mail)
    # m1 moves to a folder synced after inbox, m3 to a folder synced before archive.
    mail.changes["inbox"] = [removed("m1"), message("m3")]
    mail.changes["archive"] = [message("m1"), removed("m3")]

    sync_account(conn, ms_account)

    assert _rows(conn) == {
        ("inbox", "m1"): 1,
        ("inbox", "m2"): 0,
        ("inbox", "m3"): 0,
        ("archive", "m1"): 0,
        ("archive", "m3"): 1,
    }


def test_move_leaves_one_live_row_when_the_old_folder_fails_to_sync(
    conn: sqlite3.Connection, ms_account: Account, mail: FakeMail
) -> None:
    _loaded(conn, ms_account, mail)
    mail.changes["inbox"] = [message("m3")]
    mail.changes["archive"] = [removed("m3")]
    mail.fail_at_page = mail.pages_served + 2  # archive's page

    with pytest.raises(requests.ConnectionError):
        sync_account(conn, ms_account)

    live = [key for key, deleted in _rows(conn).items() if key[1] == "m3" and not deleted]
    assert live == [("inbox", "m3")]


def test_expired_delta_link_falls_back_to_full_load_and_flags_missing_messages(
    conn: sqlite3.Connection, ms_account: Account, mail: FakeMail
) -> None:
    _loaded(conn, ms_account, mail)
    del mail.messages["inbox"]["m2"]
    mail.expired = {"inbox"}

    sync_account(conn, ms_account)

    assert mail.requests[:2] == [("inbox", "inbox-link-1"), ("inbox", "filtered")]
    assert _rows(conn) == {("inbox", "m1"): 0, ("inbox", "m2"): 1, ("archive", "m3"): 0}
    assert _cursor(conn, ms_account, "inbox") == "inbox-link-4"


def test_full_load_commits_per_page_and_a_rerun_completes_it(
    conn: sqlite3.Connection, ms_account: Account, mail: FakeMail
) -> None:
    mail.page_size = 2
    for message_id in ("m1", "m2", "m3", "m4", "m5"):
        mail.add("inbox", message_id)
    mail.fail_at_page = 2

    with pytest.raises(requests.ConnectionError):
        sync_account(conn, ms_account)
    assert set(_rows(conn)) == {("inbox", "m1"), ("inbox", "m2")}  # the first page was committed
    assert _cursor(conn, ms_account, "inbox") is None

    mail.fail_at_page = None
    sync_account(conn, ms_account)

    assert {key[1] for key in _rows(conn)} == {"m1", "m2", "m3", "m4", "m5"}
    assert _cursor(conn, ms_account, "inbox") is not None
    statuses = [r["status"] for r in conn.execute("SELECT status FROM lm_job_runs ORDER BY id")]
    assert statuses == ["failed", "succeeded"]


def test_folder_reaching_the_filter_cap_is_loaded_again_unfiltered(
    conn: sqlite3.Connection, ms_account: Account, mail: FakeMail, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(api, "FILTER_CAP", 2)
    for message_id in ("m1", "m2", "m3"):
        mail.add("inbox", message_id)
    mail.add("inbox", "old", received=OLD)

    sync_account(conn, ms_account)

    assert mail.requests[:2] == [("inbox", "filtered"), ("inbox", "unfiltered")]
    assert _rows(conn) == {("inbox", "m1"): 0, ("inbox", "m2"): 0, ("inbox", "m3"): 0}


def test_changes_of_older_messages_are_left_out(
    conn: sqlite3.Connection, ms_account: Account, mail: FakeMail
) -> None:
    _loaded(conn, ms_account, mail)
    mail.changes["inbox"] = [message("old", OLD, isRead=True)]  # Graph reports read-state changes

    sync_account(conn, ms_account)

    assert ("inbox", "old") not in _rows(conn)


def test_vanished_folder_has_its_messages_flagged_and_is_reloaded_when_back(
    conn: sqlite3.Connection, ms_account: Account, mail: FakeMail
) -> None:
    _loaded(conn, ms_account, mail)
    mail.folders = ["inbox"]  # e.g. archive was deleted, so moved below Deleted Items

    sync_account(conn, ms_account)
    assert _rows(conn)[("archive", "m3")] == 1

    mail.folders = ["inbox", "archive"]
    mail.requests.clear()
    sync_account(conn, ms_account)

    assert ("archive", "filtered") in mail.requests
    assert _rows(conn)[("archive", "m3")] == 0


def test_sync_is_recorded_as_job_run(
    conn: sqlite3.Connection, ms_account: Account, mail: FakeMail
) -> None:
    mail.add("inbox", "m1")
    mail.add("archive", "m2")

    sync_account(conn, ms_account)

    row = conn.execute("SELECT * FROM lm_job_runs").fetchone()
    assert (row["job_name"], row["scope"], row["status"], row["items_processed"]) == (
        "ingest.outlook_mail",
        "microsoft:me@work.example",
        "succeeded",
        2,
    )

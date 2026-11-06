from zoneinfo import ZoneInfo

import pytest

from bubble_ingest.microsoft import due_dates
from bubble_ingest.microsoft.todo.mapping import tasklist_to_item, to_item


@pytest.fixture
def prague(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(due_dates, "LOCAL_ZONE", ZoneInfo("Europe/Prague"))


def _due(date_time: str, time_zone: str = "UTC") -> dict[str, str]:
    return {"dateTime": date_time, "timeZone": time_zone}


def test_task_is_due_on_its_day() -> None:
    task = {
        "id": "t1",
        "title": "Call back",
        "status": "notStarted",
        "dueDateTime": _due("2026-11-10T12:00:00.0000000"),
        "body": {"content": "about the offer", "contentType": "text"},
    }

    item = to_item("list1", task)

    assert (item.source, item.kind) == ("microsoft_todo", "task")
    assert (item.container_id, item.external_id, item.title) == ("list1", "t1", "Call back")
    assert (item.starts_at, item.ends_at) == ("2026-11-10", None)
    assert not item.deleted
    assert item.payload == task


def test_due_midnight_set_in_prague_is_that_day(prague: None) -> None:
    item = to_item("list1", {"id": "t1", "dueDateTime": _due("2026-11-09T23:00:00.0000000")})

    assert item.starts_at == "2026-11-10"


def test_due_in_a_named_zone_is_read_in_that_zone(prague: None) -> None:
    due = _due("2026-11-10T00:00:00.0000000", "America/New_York")  # 06:00 in Prague

    assert to_item("list1", {"id": "t1", "dueDateTime": due}).starts_at == "2026-11-10"


def test_due_in_an_unknown_zone_keeps_its_date(prague: None) -> None:
    due = _due("2026-11-10T23:30:00.0000000", "Pacific Standard Time")

    assert to_item("list1", {"id": "t1", "dueDateTime": due}).starts_at == "2026-11-10"


def test_task_without_due_date_has_no_start() -> None:
    assert to_item("list1", {"id": "t1", "title": "Someday"}).starts_at is None


def test_removed_task_is_deleted() -> None:
    item = to_item("list1", {"id": "t1", "@removed": {"reason": "deleted"}})

    assert item.deleted


def test_task_list_is_a_container_item() -> None:
    tasklist = {"id": "l1", "displayName": "Flagged email", "wellknownListName": "flaggedEmails"}

    item = tasklist_to_item(tasklist)

    assert (item.source, item.kind) == ("microsoft_todo", "tasklist")
    assert (item.container_id, item.external_id, item.title) == ("", "l1", "Flagged email")

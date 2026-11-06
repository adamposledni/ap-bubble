from zoneinfo import ZoneInfo

import pytest

from bubble_ingest.microsoft import due_dates
from bubble_ingest.microsoft.planner.mapping import plan_to_item, to_item


@pytest.fixture
def prague(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(due_dates, "LOCAL_ZONE", ZoneInfo("Europe/Prague"))


def test_task_sits_in_its_plan_and_is_due_on_its_day() -> None:
    task = {
        "id": "t1",
        "planId": "p1",
        "title": "Write report",
        "percentComplete": 50,
        "dueDateTime": "2026-11-10T12:00:00Z",
    }

    item = to_item(task)

    assert (item.source, item.kind) == ("planner", "task")
    assert (item.container_id, item.external_id, item.title) == ("p1", "t1", "Write report")
    assert (item.starts_at, item.ends_at) == ("2026-11-10", None)
    assert not item.deleted
    assert item.payload == task


def test_due_midnight_set_in_prague_is_that_day(prague: None) -> None:
    item = to_item({"id": "t1", "planId": "p1", "dueDateTime": "2026-11-09T23:00:00Z"})

    assert item.starts_at == "2026-11-10"


def test_task_without_due_date_has_no_start() -> None:
    item = to_item({"id": "t1", "planId": "p1"})

    assert item.starts_at is None


def test_plan_is_a_container_item() -> None:
    item = plan_to_item({"id": "p1", "title": "Project X"})

    assert (item.source, item.kind) == ("planner", "plan")
    assert (item.container_id, item.external_id, item.title) == ("", "p1", "Project X")

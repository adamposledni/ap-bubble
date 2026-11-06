from typing import Any

import pytest

from bubble_ingest.microsoft.calendar.mapping import calendar_to_item, to_item


def _utc(day_and_time: str) -> dict[str, str]:
    return {"dateTime": f"2026-03-{day_and_time}:00.0000000", "timeZone": "UTC"}


def _event(**fields: Any) -> dict[str, Any]:
    return {"id": "e1", "subject": "Review", "type": "singleInstance", "isAllDay": False} | fields


def test_timed_event_gets_vault_utc_times() -> None:
    item = to_item("cal", _event(start=_utc("05T09:00"), end=_utc("05T10:30")))

    assert (item.source, item.kind, item.container_id) == ("outlook_calendar", "event", "cal")
    assert (item.external_id, item.title) == ("e1", "Review")
    assert (item.starts_at, item.ends_at) == (
        "2026-03-05T09:00:00+00:00",
        "2026-03-05T10:30:00+00:00",
    )
    assert not item.deleted


def test_all_day_event_keeps_its_dates() -> None:
    event = _event(isAllDay=True, start=_utc("05T00:00"), end=_utc("07T00:00"))

    item = to_item("cal", event)

    assert (item.starts_at, item.ends_at) == ("2026-03-05", "2026-03-07")


def test_removed_entry_of_a_delta_is_deleted() -> None:
    item = to_item("cal", {"id": "e1", "@removed": {"reason": "deleted"}})

    assert item.deleted
    assert (item.title, item.starts_at) == (None, None)


def test_cancelled_event_is_deleted() -> None:
    event = _event(isCancelled=True, start=_utc("05T09:00"), end=_utc("05T10:00"))

    assert to_item("cal", event).deleted


def test_times_outside_utc_are_rejected() -> None:
    when = {"dateTime": "2026-03-05T09:00:00.0000000", "timeZone": "Central Europe Standard Time"}

    with pytest.raises(ValueError):
        to_item("cal", _event(start=when, end=when))


def test_calendar_is_a_container_named_like_in_outlook() -> None:
    item = calendar_to_item({"id": "cal", "name": "Calendar", "isDefaultCalendar": True})

    assert (item.container_id, item.external_id, item.kind, item.title) == (
        "",
        "cal",
        "calendar",
        "Calendar",
    )

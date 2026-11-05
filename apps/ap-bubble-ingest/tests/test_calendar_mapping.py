from bubble_ingest.google.calendar.mapping import to_item


def test_timed_event_gets_utc_times() -> None:
    item = to_item(
        "cal",
        {
            "id": "e1",
            "status": "confirmed",
            "summary": "Lunch",
            "start": {"dateTime": "2026-03-05T12:00:00+01:00"},
            "end": {"dateTime": "2026-03-05T13:00:00+01:00"},
        },
    )

    assert (item.container_id, item.external_id, item.title) == ("cal", "e1", "Lunch")
    assert (item.starts_at, item.ends_at) == (
        "2026-03-05T11:00:00+00:00",
        "2026-03-05T12:00:00+00:00",
    )
    assert not item.deleted


def test_all_day_event_keeps_its_dates() -> None:
    item = to_item(
        "cal", {"id": "e1", "start": {"date": "2026-03-05"}, "end": {"date": "2026-03-06"}}
    )

    assert (item.starts_at, item.ends_at) == ("2026-03-05", "2026-03-06")


def test_cancelled_event_is_deleted() -> None:
    item = to_item("cal", {"id": "e1", "status": "cancelled"})

    assert item.deleted
    assert item.starts_at is None

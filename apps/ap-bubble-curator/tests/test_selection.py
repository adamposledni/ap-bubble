from typing import Any

from bubble_curator.changes import ChangedItem
from bubble_curator.selection import in_window, is_noise

SINCE = "2026-10-07T00:00:00+00:00"


def _item(
    source: str, kind: str, payload: dict[str, Any] | None = None, **fields: Any
) -> ChangedItem:
    values: dict[str, Any] = {
        "id": 1,
        "account_id": 1,
        "context": "work",
        "source": source,
        "kind": kind,
        "container_id": "c",
        "title": "t",
        "starts_at": "2026-11-01T10:00:00+00:00",
        "ends_at": None,
        "deleted": False,
        "payload": payload or {},
    }
    return ChangedItem(**(values | fields))


def test_noise_is_skipped() -> None:
    assert is_noise(_item("teams_chats", "chat_message", {"messageType": "systemEventMessage"}))
    assert is_noise(_item("gmail", "mail", {"labelIds": ["INBOX", "CATEGORY_PROMOTIONS"]}))
    unsubscribe = {"payload": {"headers": [{"name": "List-Unsubscribe", "value": "<mailto:x>"}]}}
    assert is_noise(_item("gmail", "mail", unsubscribe))
    assert is_noise(_item("outlook_mail", "mail", {"inferenceClassification": "other"}))
    assert is_noise(_item("outlook_calendar", "event", {"type": "seriesMaster"}))
    assert is_noise(_item("teams_chats", "chat", {}))
    assert is_noise(_item("gmail", "mail", {}, deleted=True))


def test_real_content_is_kept() -> None:
    assert not is_noise(_item("teams_chats", "chat_message", {"messageType": "message"}))
    assert not is_noise(_item("gmail", "mail", {"labelIds": ["INBOX", "IMPORTANT"]}))
    assert not is_noise(_item("outlook_mail", "mail", {"inferenceClassification": "focused"}))
    assert not is_noise(_item("outlook_calendar", "event", {"type": "occurrence"}))


def test_window_keeps_recent_items_upcoming_events_open_tasks_and_contacts() -> None:
    old = "2026-03-01T10:00:00+00:00"
    assert not in_window(_item("gmail", "mail", starts_at=old), SINCE)
    assert in_window(_item("gmail", "mail"), SINCE)
    assert in_window(_item("google_calendar", "event", starts_at=old, ends_at="2026-12-01"), SINCE)
    assert in_window(
        _item("google_tasks", "task", {"status": "needsAction"}, starts_at=None), SINCE
    )
    done_long_ago = {"status": "completed", "updated": "2026-02-01T00:00:00Z"}
    assert not in_window(_item("google_tasks", "task", done_long_ago, starts_at=None), SINCE)
    assert in_window(_item("google_contacts", "contact", starts_at=None), SINCE)


def test_events_of_skipped_calendars_are_noise() -> None:
    holidays = "cs.czech#holiday@group.v.calendar.google.com"
    shifts = "quh6h0ajl2qtrouii90g38el9davgdt3@import.calendar.google.com"
    assert is_noise(_item("google_calendar", "event", container_id=holidays))
    assert is_noise(_item("google_calendar", "event", container_id=shifts))
    assert not is_noise(_item("google_calendar", "event", container_id="adam@example.com"))


def test_service_contacts_are_noise_and_real_ones_are_kept() -> None:
    def contact(**payload: Any) -> ChangedItem:
        return _item("google_contacts", "contact", payload)

    assert is_noise(contact())
    assert is_noise(contact(phoneNumbers=[{"value": "155"}]))
    assert is_noise(contact(phoneNumbers=[{"value": "112"}, {"value": "*77"}]))
    assert not is_noise(contact(phoneNumbers=[{"value": "+420 466 100 777"}]))
    assert not is_noise(contact(emailAddresses=[{"value": "a@b.cz"}]))

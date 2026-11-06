import base64
from typing import Any

from bubble_core.inputs import Input
from bubble_curator.changes import ChangedItem
from bubble_curator.units import build_units


def _item(
    item_id: int, source: str, kind: str, payload: dict[str, Any], **fields: Any
) -> ChangedItem:
    values: dict[str, Any] = {
        "id": item_id,
        "account_id": 1,
        "context": "work",
        "source": source,
        "kind": kind,
        "container_id": "chat-1",
        "title": None,
        "starts_at": f"2026-11-0{item_id}T10:00:00+00:00",
        "ends_at": None,
        "deleted": False,
        "payload": payload,
    }
    return ChangedItem(**(values | fields))


def _outlook_mail(item_id: int, conversation: str) -> ChangedItem:
    payload = {
        "conversationId": conversation,
        "from": {"emailAddress": {"name": "Petr", "address": "petr@x.cz"}},
        "toRecipients": [{"emailAddress": {"name": "Adam", "address": "adam@x.cz"}}],
        "body": {"contentType": "text", "content": f"message {item_id}"},
    }
    return _item(item_id, "outlook_mail", "mail", payload, title="Contract")


def _chat(item_id: int, html: str) -> ChangedItem:
    payload = {
        "from": {"user": {"displayName": "Jana"}},
        "body": {"contentType": "html", "content": html},
    }
    return _item(item_id, "teams_chats", "chat_message", payload)


def test_mail_of_one_conversation_is_one_unit_in_time_order() -> None:
    [unit] = build_units([], [_outlook_mail(2, "conv"), _outlook_mail(1, "conv")], {})

    assert unit.heading == "Mail thread: Contract (work, Outlook)"
    assert unit.item_ids == [1, 2]
    assert unit.body.index("message 1") < unit.body.index("message 2")
    assert "From: Petr <petr@x.cz> — To: Adam <adam@x.cz>" in unit.body


def test_gmail_text_is_decoded_from_the_plain_part() -> None:
    data = base64.urlsafe_b64encode(b"Ahoj Adame").decode().rstrip("=")
    payload = {
        "threadId": "t1",
        "payload": {
            "headers": [{"name": "From", "value": "Eva <eva@x.cz>"}],
            "parts": [{"mimeType": "text/plain", "body": {"data": data}}],
        },
    }

    [unit] = build_units([], [_item(1, "gmail", "mail", payload, title="Hi")], {})

    assert "Ahoj Adame" in unit.body and "From: Eva <eva@x.cz>" in unit.body


def test_chat_messages_are_grouped_per_chat_and_day_without_empty_ones() -> None:
    items = [_chat(1, "<p>Hi</p>"), _chat(2, "<p>See you</p>"), _chat(3, "<img src='x'>")]

    units = build_units([], items, {(1, "chat-1"): "Jana Nováková"})

    assert [u.heading.split(" — ")[0] for u in units] == ["Teams chat: Jana Nováková"] * 2
    assert [u.item_ids for u in units] == [[1], [2]]
    assert "Jana: Hi" in units[0].body


def test_inputs_come_first_then_items_by_time() -> None:
    note = Input(
        7, "Petr's birthday is 3 May", "queued", None, "2026-11-06T07:00:00+00:00", None, []
    )
    event = _item(1, "google_calendar", "event", {"summary": "Lunch"}, title="Lunch")

    units = build_units([note], [event], {})

    assert units[0].input_ids == [7] and "Petr's birthday" in units[0].body
    assert units[1].heading.startswith("Event: Lunch")


def _occurrence(item_id: int, kind: str = "occurrence", series: str = "s1") -> ChangedItem:
    payload = {
        "type": kind,
        "seriesMasterId": series,
        "location": {"displayName": "Room 1"},
        "organizer": {"emailAddress": {"name": "Petr"}},
    }
    return _item(
        item_id, "outlook_calendar", "event", payload, title="Standup",
        starts_at=f"2026-11-0{item_id}T10:00:00+00:00",
    )  # fmt: skip


def test_occurrences_of_a_series_are_one_unit_with_count_and_range() -> None:
    items = [_occurrence(3), _occurrence(1), _occurrence(2)]

    [unit] = build_units([], items, {})

    assert unit.heading == "Recurring event: Standup [l0:1] (work)"
    assert unit.item_ids == [1, 2, 3]
    assert unit.sort_key == "12026-11-01T10:00:00+00:00"
    assert "Where: Room 1" in unit.body and "Organizer: Petr" in unit.body
    assert "- Occurrences: 3, from " in unit.body


def test_different_series_are_separate_units() -> None:
    units = build_units([], [_occurrence(1), _occurrence(2, series="s2")], {})

    assert [u.item_ids for u in units] == [[1], [2]]


def test_exceptions_and_single_instances_stay_individual() -> None:
    items = [_occurrence(1), _occurrence(2, "exception"), _occurrence(3, "singleInstance")]

    units = build_units([], items, {})

    assert [u.item_ids for u in units] == [[1], [2], [3]]
    assert [u.heading.split(":")[0] for u in units] == ["Recurring event", "Event", "Event"]

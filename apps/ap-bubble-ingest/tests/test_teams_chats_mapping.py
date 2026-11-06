from typing import Any

from bubble_ingest.microsoft.chats.mapping import chat_to_item, to_item

ME = "user-me"


def _member(user_id: str, name: str | None) -> dict[str, Any]:
    return {"id": f"membership-{user_id}", "userId": user_id, "displayName": name, "roles": []}


def _chat(topic: str | None, *members: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "19:chat1@thread.v2",
        "topic": topic,
        "chatType": "group",
        "members": list(members),
        "members@odata.context": "https://graph/$metadata#members",
        "lastMessagePreview": {"id": "m9", "createdDateTime": "2026-03-05T09:30:00Z"},
        "lastMessagePreview@odata.context": "https://graph/$metadata#preview",
        "viewpoint": {"isHidden": False},
    }


def _message(**fields: Any) -> dict[str, Any]:
    return {
        "id": "1772703000123",
        "messageType": "message",
        "createdDateTime": "2026-03-05T09:30:00.123Z",
        "lastModifiedDateTime": "2026-03-05T09:31:00.5Z",
        "deletedDateTime": None,
        "body": {"contentType": "html", "content": "<p>See you at <b>ten</b></p>"},
        "eventDetail": None,
        **fields,
    }


def test_chat_with_topic_is_titled_by_it() -> None:
    chat = _chat("Project X", _member(ME, "Me"), _member("u2", "Bob"))

    item = chat_to_item(chat, ME)

    assert (item.source, item.kind, item.container_id) == ("teams_chats", "chat", "")
    assert (item.external_id, item.title) == ("19:chat1@thread.v2", "Project X")
    assert not item.deleted


def test_chat_payload_keeps_members_but_not_the_last_message_preview() -> None:
    item = chat_to_item(_chat("Project X", _member("u2", "Bob")), ME)

    assert item.payload["members"] == [_member("u2", "Bob")]
    assert item.payload["viewpoint"] == {"isHidden": False}
    assert not any(key.startswith("lastMessagePreview") for key in item.payload)
    assert not any(key.endswith("@odata.context") for key in item.payload)


def test_chat_payload_and_title_do_not_depend_on_the_order_of_members() -> None:
    bob, ann, me = _member("u2", "Bob"), _member("u3", "Ann"), _member(ME, "Me")

    one, other = (
        chat_to_item(_chat(None, bob, me, ann), ME),
        chat_to_item(_chat(None, ann, bob), ME),
    )

    assert one.payload["members"] == [bob, ann, me]  # by membership id
    assert other.payload["members"] == [bob, ann]
    assert one.title == other.title == "Ann, Bob"


def test_chat_without_topic_is_titled_by_the_other_named_members() -> None:
    chat = _chat(None, _member(ME, "Me"), _member("u2", "Bob"), _member("u3", None))

    assert chat_to_item(chat, ME).title == "Bob"


def test_title_of_a_large_chat_names_five_members_and_counts_the_rest() -> None:
    members = [_member(f"u{i}", f"Person {i}") for i in reversed(range(7))]

    title = chat_to_item(_chat(None, *members), ME).title

    assert title == "Person 0, Person 1, Person 2, Person 3, Person 4 +2"


def test_chat_with_nobody_else_has_no_title() -> None:
    assert chat_to_item(_chat(None, _member(ME, "Me")), ME).title is None


def test_message_maps_onto_an_item_with_a_text_title() -> None:
    message = _message()

    item = to_item("19:chat1@thread.v2", message)

    assert (item.source, item.kind) == ("teams_chats", "chat_message")
    assert (item.container_id, item.external_id) == ("19:chat1@thread.v2", "1772703000123")
    assert item.title == "See you at ten"
    assert (item.starts_at, item.ends_at) == ("2026-03-05T09:30:00+00:00", None)
    assert not item.deleted
    assert item.payload == message


def test_soft_deleted_message_is_deleted() -> None:
    message = _message(deletedDateTime="2026-03-06T08:00:00Z", body={"content": ""})

    item = to_item("c1", message)

    assert item.deleted
    assert item.title is None


def test_system_event_message_is_titled_by_its_event() -> None:
    event = {"@odata.type": "#microsoft.graph.callEndedEventMessageDetail", "callId": "x"}
    message = _message(
        messageType="systemEventMessage",
        body={"contentType": "html", "content": "<systemEventMessage/>"},
        eventDetail=event,
    )

    assert to_item("c1", message).title == "[system] callEnded"


def test_event_message_without_detail_is_titled_by_its_type() -> None:
    message = _message(messageType="unknownFutureValue", body=None)

    assert to_item("c1", message).title == "[system] unknownFutureValue"

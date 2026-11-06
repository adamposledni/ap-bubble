"""Maps Teams chats and chat messages onto L0 items.

A message's title is a short plain-text start of its body (no subject in chats), so lists and
keyword search show what was said without parsing the payload. System event messages (members
added, call ended, chat renamed, ...) are kept, titled '[system] <event>', e.g.
'[system] callEnded', so readers can recognise or filter them; the payload keeps messageType
and eventDetail.
"""

from bubble_core.clock import to_utc
from bubble_core.items import Item
from bubble_ingest.l0_sync import CONTAINER_LIST_ID
from bubble_ingest.microsoft.chats.text import snippet
from bubble_ingest.microsoft.graph import Json

SOURCE = "teams_chats"
KIND = "chat_message"
CHAT_KIND = "chat"
SYSTEM_TITLE_PREFIX = "[system] "
TITLE_MEMBERS = 5  # names shown in the title of a chat without a topic
_USER_MESSAGE = "message"  # messageType of what people write; the others are events
# The preview changes with every message (which L0 holds anyway); the rest is OData noise.
_CHAT_DROPPED_KEYS = {
    "lastMessagePreview",
    "lastMessagePreview@odata.context",
    "members@odata.context",
}
_EVENT_TYPE_PREFIX = "#microsoft.graph."
_EVENT_TYPE_SUFFIX = "EventMessageDetail"


def chat_to_item(chat: Json, my_user_id: str) -> Item:
    return Item(
        source=SOURCE,
        container_id=CONTAINER_LIST_ID,
        external_id=chat["id"],
        kind=CHAT_KIND,
        title=_chat_title(chat, my_user_id),
        starts_at=None,
        ends_at=None,
        deleted=False,
        payload=_stable_chat(chat),
    )


def to_item(chat_id: str, message: Json) -> Item:
    return Item(
        source=SOURCE,
        container_id=chat_id,
        external_id=message["id"],
        kind=KIND,
        title=_message_title(message),
        starts_at=to_utc(message["createdDateTime"]),
        ends_at=None,
        deleted=message.get("deletedDateTime") is not None,
        payload=message,
    )


def _stable_chat(chat: Json) -> Json:
    """The chat as a payload that changes only when the chat does.

    Graph returns the members in a different order on every call, so they are sorted.
    """
    payload = {key: value for key, value in chat.items() if key not in _CHAT_DROPPED_KEYS}
    if payload.get("members"):
        payload["members"] = sorted(payload["members"], key=lambda member: member["id"])
    return payload


def _chat_title(chat: Json, my_user_id: str) -> str | None:
    """The topic, else the other members' names (Graph expands at most about 25 members)."""
    if chat.get("topic"):
        return chat["topic"]
    names = sorted(
        member["displayName"]
        for member in chat.get("members") or []
        if member.get("userId") != my_user_id and member.get("displayName")
    )
    shown = ", ".join(names[:TITLE_MEMBERS])
    hidden = len(names) - TITLE_MEMBERS
    return f"{shown} +{hidden}" if hidden > 0 else shown or None


def _message_title(message: Json) -> str | None:
    if message.get("messageType", _USER_MESSAGE) != _USER_MESSAGE:
        return SYSTEM_TITLE_PREFIX + _event_name(message)
    return snippet(message.get("body"))


def _event_name(message: Json) -> str:
    """E.g. 'callEnded' for eventDetail of type '#microsoft.graph.callEndedEventMessageDetail'."""
    event_type = (message.get("eventDetail") or {}).get("@odata.type")
    if not event_type:
        return message.get("messageType") or "event"
    return event_type.removeprefix(_EVENT_TYPE_PREFIX).removesuffix(_EVENT_TYPE_SUFFIX)

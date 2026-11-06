"""Mail (Outlook and Gmail) as units: one per conversation, its messages in time order."""

from collections import defaultdict
from typing import Any

from bubble_core import gmail_text
from bubble_curator.changes import ChangedItem
from bubble_curator.unit import Unit, clip, local_time, ref

_SOURCE_NAMES = {"outlook_mail": "Outlook", "gmail": "Gmail"}


def mail_units(items: list[ChangedItem]) -> list[Unit]:
    threads: dict[tuple[int, str], list[ChangedItem]] = defaultdict(list)
    for item in items:
        threads[(item.account_id, _thread_id(item))].append(item)
    return [_unit(sorted(msgs, key=lambda m: m.starts_at or "")) for msgs in threads.values()]


def _unit(messages: list[ChangedItem]) -> Unit:
    first = messages[0]
    subject = first.title or "(no subject)"
    heading = f"Mail thread: {subject} ({first.context}, {_SOURCE_NAMES[first.source]})"
    body = "\n\n".join(_message(m) for m in messages)
    return Unit(heading, body, sort_key=f"1{first.starts_at}", item_ids=[m.id for m in messages])


def _message(item: ChangedItem) -> str:
    sender, recipients, text = _parts(item)
    line = f"[{ref(item.id)}] {local_time(item.starts_at)} — From: {sender} — To: {recipients}"
    return f"{line}\n{clip(text)}"


def _parts(item: ChangedItem) -> tuple[str, str, str]:
    payload = item.payload
    if item.source == "gmail":
        to = ", ".join(
            filter(None, [gmail_text.header(payload, "To"), gmail_text.header(payload, "Cc")])
        )
        return gmail_text.header(payload, "From"), to, gmail_text.text_of(payload)
    sender = _address(payload.get("from"))
    to = ", ".join(
        _address(r) for r in payload.get("toRecipients", []) + payload.get("ccRecipients", [])
    )
    return sender, to, (payload.get("body") or {}).get("content", "")


def _address(recipient: dict[str, Any] | None) -> str:
    email = (recipient or {}).get("emailAddress", {})
    name, address = email.get("name", ""), email.get("address", "")
    return f"{name} <{address}>" if name and address and name != address else name or address


def _thread_id(item: ChangedItem) -> str:
    payload = item.payload
    return payload.get("conversationId") or payload.get("threadId") or str(item.id)

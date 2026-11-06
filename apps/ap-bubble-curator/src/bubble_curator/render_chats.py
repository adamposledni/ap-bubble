"""Teams chat messages as units: one per chat and local day, messages in time order."""

from collections import defaultdict

from bubble_core.text import body_text
from bubble_curator.changes import ChangedItem
from bubble_curator.unit import Unit, clip, local_time, ref

type ChatTitles = dict[tuple[int, str], str | None]  # (account id, chat id) -> title
type Message = tuple[ChangedItem, str]  # the item and its body as text


def chat_units(items: list[ChangedItem], titles: ChatTitles) -> list[Unit]:
    """Messages without text (e.g. only an attachment) are left out."""
    days: dict[tuple[int, str, str], list[Message]] = defaultdict(list)
    for item in items:
        if text := body_text(item.payload.get("body")).strip():
            day = local_time(item.starts_at)[:10]
            days[(item.account_id, item.container_id, day)].append((item, text))
    units = []
    for (account_id, chat_id, day), messages in days.items():
        messages.sort(key=lambda message: message[0].starts_at or "")
        units.append(_unit(messages, titles.get((account_id, chat_id)), day))
    return units


def _unit(messages: list[Message], title: str | None, day: str) -> Unit:
    first = messages[0][0]
    heading = f"Teams chat: {title or 'untitled chat'} — {day} ({first.context})"
    body = "\n".join(_line(item, text) for item, text in messages)
    item_ids = [item.id for item, _ in messages]
    return Unit(heading, body, sort_key=f"1{first.starts_at}", item_ids=item_ids)


def _line(item: ChangedItem, text: str) -> str:
    sender = (item.payload.get("from") or {}).get("user") or {}
    time = local_time(item.starts_at)[11:]
    return f"[{ref(item.id)}] {time} {sender.get('displayName') or 'unknown'}: " + clip(
        text
    ).replace("\n", " ")

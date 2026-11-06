"""Readable text of an L0 item: the mail, chat or event body, or a task's notes."""

from typing import Any

from bubble_core import gmail_text
from bubble_core.text import body_text

_GMAIL = "gmail"
_PLAIN_KEYS = ("description", "notes", "bodyPreview")  # Google events and tasks, Graph previews


def item_text(source: str, payload: dict[str, Any]) -> str | None:
    """The item's own text, or None when it has none (contacts, empty bodies, ...)."""
    if source == _GMAIL:
        return gmail_text.text_of(payload).strip() or None
    body = payload.get("body")
    if isinstance(body, dict) and (text := body_text(body).strip()):
        return text
    return next((str(payload[key]).strip() for key in _PLAIN_KEYS if payload.get(key)), None)

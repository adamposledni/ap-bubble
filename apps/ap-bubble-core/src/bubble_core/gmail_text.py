"""Headers and plain text of Gmail messages stored as format=full payloads."""

import base64
from collections.abc import Iterator
from typing import Any

from bubble_core.text import html_to_text


def header(message: dict[str, Any], name: str) -> str:
    for item in message.get("payload", {}).get("headers", []):
        if item.get("name", "").lower() == name.lower():
            return item.get("value", "")
    return ""


def text_of(message: dict[str, Any]) -> str:
    """The text/plain part, else the text/html part as text, else Gmail's snippet."""
    parts = list(_parts(message.get("payload", {})))
    plain = next((p for p in parts if p.get("mimeType") == "text/plain"), None)
    if plain:
        return _decode(plain)
    html = next((p for p in parts if p.get("mimeType") == "text/html"), None)
    return html_to_text(_decode(html)) if html else message.get("snippet", "")


def _parts(part: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """The MIME part and all parts nested in it."""
    yield part
    for child in part.get("parts", []):
        yield from _parts(child)


def _decode(part: dict[str, Any]) -> str:
    data = part.get("body", {}).get("data", "")
    if not data:
        return ""
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", "replace")

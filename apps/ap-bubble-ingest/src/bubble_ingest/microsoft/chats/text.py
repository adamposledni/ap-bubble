"""Short plain-text snippets of Teams message bodies (HTML or text), used as L0 titles."""

from typing import Any

from bubble_core.text import body_text

SNIPPET_LENGTH = 80
_ELLIPSIS = "…"


def snippet(body: dict[str, Any] | None) -> str | None:
    """The first SNIPPET_LENGTH characters of the body as one line of text; None when empty."""
    text = " ".join(body_text(body).split())
    if len(text) <= SNIPPET_LENGTH:
        return text or None
    return text[: SNIPPET_LENGTH - len(_ELLIPSIS)].rstrip() + _ELLIPSIS

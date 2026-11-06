"""Short plain-text snippets of Teams message bodies (HTML or text), used as L0 titles."""

from html.parser import HTMLParser
from typing import Any

SNIPPET_LENGTH = 80
_ELLIPSIS = "…"
_BREAKING_TAGS = {"br", "p", "div", "li", "tr", "td", "h1", "h2", "h3"}
_QUOTE_TAG = "blockquote"  # a reply quotes the message it answers; that text is not its own


def snippet(body: dict[str, Any] | None) -> str | None:
    """The first SNIPPET_LENGTH characters of the body as one line of text; None when empty."""
    text = " ".join(_plain_text(body or {}).split())
    if len(text) <= SNIPPET_LENGTH:
        return text or None
    return text[: SNIPPET_LENGTH - len(_ELLIPSIS)].rstrip() + _ELLIPSIS


def _plain_text(body: dict[str, Any]) -> str:
    content = body.get("content") or ""
    if body.get("contentType") == "text":
        return content
    collector = _TextCollector()
    collector.feed(content)
    collector.close()
    return "".join(collector.parts)


class _TextCollector(HTMLParser):
    """Collects the text of an HTML fragment, without quoted replies; entities are decoded."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._quote_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == _QUOTE_TAG:
            self._quote_depth += 1
        self._break(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == _QUOTE_TAG and self._quote_depth:
            self._quote_depth -= 1
        self._break(tag)

    def handle_data(self, data: str) -> None:
        if not self._quote_depth:
            self.parts.append(data)

    def _break(self, tag: str) -> None:
        if tag in _BREAKING_TAGS:
            self.parts.append(" ")

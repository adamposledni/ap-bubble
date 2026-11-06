"""Plain text from HTML fragments (mail and chat bodies), without quoted replies."""

import re
from html.parser import HTMLParser
from typing import Any

_BREAKING_TAGS = {"br", "p", "div", "li", "tr", "td", "h1", "h2", "h3", "h4", "hr"}
_QUOTE_TAG = "blockquote"  # a reply quotes the message it answers; that text is not its own
_BLANK_LINES = re.compile(r"\n\s*\n\s*\n+")


def body_text(body: dict[str, Any] | None) -> str:
    """Text of a Graph itemBody ({contentType, content}), HTML or plain."""
    body = body or {}
    content = body.get("content") or ""
    return content if body.get("contentType") == "text" else html_to_text(content)


def html_to_text(html: str) -> str:
    """The text of an HTML fragment, a line per block, entities decoded, quoted replies left out."""
    collector = _TextCollector()
    collector.feed(html)
    collector.close()
    lines = [line.strip() for line in "".join(collector.parts).splitlines()]
    return _BLANK_LINES.sub("\n\n", "\n".join(lines)).strip()


class _TextCollector(HTMLParser):
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
            self.parts.append("\n")

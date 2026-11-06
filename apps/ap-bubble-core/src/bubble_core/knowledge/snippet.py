"""A short excerpt of a text around the first match, split into matched and other parts."""

from dataclasses import dataclass

from bubble_core.knowledge.fold import find_all

_LENGTH = 180  # characters of text in a snippet
_LEAD = 60  # of them before the first match
_ELLIPSIS = "…"


@dataclass(frozen=True)
class SnippetPart:
    text: str
    match: bool


def snippet(text: str, terms: list[str]) -> list[SnippetPart]:
    """The excerpt around the first match of any folded term (else the start of text)."""
    if not text:
        return []
    matches = find_all(text, terms)
    first = matches[0][0] if matches else 0
    excerpt = _excerpt(text, first)
    return _parts(excerpt, find_all(excerpt, terms))


def _excerpt(text: str, first: int) -> str:
    start = max(0, first - _LEAD)
    if start:
        space = text.find(" ", start, first)
        start = space + 1 if space >= 0 else start
    end = min(len(text), start + _LENGTH)
    if end < len(text):
        space = text.rfind(" ", first, end)
        end = space if space > first else end
    prefix = _ELLIPSIS if start else ""
    suffix = _ELLIPSIS if end < len(text) else ""
    return prefix + text[start:end].strip() + suffix


def _parts(text: str, spans: list[tuple[int, int]]) -> list[SnippetPart]:
    parts: list[SnippetPart] = []
    position = 0
    for start, end in spans:
        if start > position:
            parts.append(SnippetPart(text[position:start], match=False))
        parts.append(SnippetPart(text[start:end], match=True))
        position = end
    if position < len(text):
        parts.append(SnippetPart(text[position:], match=False))
    return parts

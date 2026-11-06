"""Plain text of a knowledge file's markdown body: what search matches and snippets show."""

import re

_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MARKUP = re.compile(r"\*\*|__|`")
_LIST_MARKER = re.compile(r"^(?:[-*+]|\d+\.)\s+")
_LINE_SEPARATOR = " · "


def plain_text(markdown: str) -> str:
    """Body lines without headings, link targets and emphasis, joined into one line."""
    lines = (_plain_line(line) for line in markdown.splitlines() if not _is_heading(line))
    return _LINE_SEPARATOR.join(line for line in lines if line)


def _is_heading(line: str) -> bool:
    return line.lstrip().startswith("#")


def _plain_line(line: str) -> str:
    text = _LINK.sub(r"\1", line.strip())
    return _LIST_MARKER.sub("", _MARKUP.sub("", text)).strip()

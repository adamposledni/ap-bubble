"""A unit: one piece of context for Claude (a note, a mail thread, a chat day, an event, ...)."""

from dataclasses import dataclass, field
from datetime import datetime

from bubble_curator.settings import FILE_CHARS, MAX_TEXT_CHARS

_ELLIPSIS = " […]"


@dataclass(frozen=True)
class Unit:
    heading: str  # one line, without the markdown hashes
    body: str
    sort_key: str  # inputs first, then by time
    item_ids: list[int] = field(default_factory=list)  # L0 rows it covers
    input_ids: list[int] = field(default_factory=list)  # L1 inputs it covers
    file_count: int = 0  # attached files Claude has to read

    @property
    def weight(self) -> int:
        """Batch size of the unit: its text plus the files Claude has to read."""
        return len(self.render()) + self.file_count * FILE_CHARS

    def render(self) -> str:
        return f"## {self.heading}\n\n{self.body.strip()}\n"


def clip(text: str, limit: int = MAX_TEXT_CHARS) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit].rstrip() + _ELLIPSIS


def local_time(timestamp: str | None) -> str:
    """'2026-11-05 14:02' in this PC's time zone; dates and unparsable values stay as they are."""
    if not timestamp or len(timestamp) <= 10:
        return timestamp or "?"
    try:
        return (
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            .astimezone()
            .strftime("%Y-%m-%d %H:%M")
        )
    except ValueError:
        return timestamp


def ref(item_id: int) -> str:
    """How a source is cited in knowledge files."""
    return f"l0:{item_id}"

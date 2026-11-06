"""L0 items as knowledge files cite them (l0:123, l0:504–519): one with its text, or a range."""

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, cast

from bubble_core.accounts import Context
from bubble_core.log import get_logger
from bubble_core.queries.item_text import item_text

MAX_RANGE = 50  # items of one range read

_SELECT = "SELECT i.*, a.email, a.context FROM l0_items i JOIN lm_accounts a ON a.id = i.account_id"

logger = get_logger(__name__)


class ItemNotFound(LookupError):
    pass


@dataclass(frozen=True)
class ItemAccount:
    email: str
    context: Context


@dataclass(frozen=True)
class ItemSummary:
    id: int
    source: str
    kind: str
    title: str | None
    starts_at: str | None
    ends_at: str | None
    deleted: bool
    account: ItemAccount
    changed_at: str


@dataclass(frozen=True)
class ItemDetail(ItemSummary):
    text: str | None  # readable text of the payload, if it has any
    payload: dict[str, Any]  # as the source delivered it


@dataclass(frozen=True)
class ItemRange:
    items: list[ItemSummary]
    truncated: bool  # the range holds more than MAX_RANGE ids


def get_item(conn: sqlite3.Connection, item_id: int) -> ItemDetail:
    row = conn.execute(f"{_SELECT} WHERE i.id = ?", (item_id,)).fetchone()
    if row is None:
        raise ItemNotFound(f"Item {item_id} not found")
    payload = json.loads(row["payload"])
    logger.debug("Read item %d (%s %s)", item_id, row["source"], row["kind"])
    return ItemDetail(
        **vars(_to_summary(row)), text=item_text(row["source"], payload), payload=payload
    )


def item_range(conn: sqlite3.Connection, first: int, last: int) -> ItemRange:
    """Items with ids first..last (both included), the first MAX_RANGE ids of it at most."""
    if last < first:
        raise ValueError(f"Range {first}–{last} ends before it starts")
    capped = min(last, first + MAX_RANGE - 1)
    rows = conn.execute(
        f"{_SELECT} WHERE i.id BETWEEN ? AND ? ORDER BY i.id", (first, capped)
    ).fetchall()
    logger.debug("Read %d items of range %d–%d (capped at %d)", len(rows), first, last, capped)
    return ItemRange([_to_summary(row) for row in rows], truncated=capped < last)


def _to_summary(row: sqlite3.Row) -> ItemSummary:
    logger.trace("Item row %d", row["id"])
    return ItemSummary(
        id=row["id"],
        source=row["source"],
        kind=row["kind"],
        title=row["title"],
        starts_at=row["starts_at"],
        ends_at=row["ends_at"],
        deleted=bool(row["deleted"]),
        account=ItemAccount(email=row["email"], context=cast(Context, row["context"])),
        changed_at=row["changed_at"],
    )

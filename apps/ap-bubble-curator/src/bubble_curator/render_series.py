"""Occurrences of a recurring Outlook event as units: one per series, not one per occurrence."""

from collections import defaultdict
from dataclasses import replace

from bubble_core.log import get_logger
from bubble_curator.changes import ChangedItem
from bubble_curator.render_records import record_unit
from bubble_curator.unit import Unit, local_time

logger = get_logger(__name__)


def is_occurrence(item: ChangedItem) -> bool:
    payload = item.payload
    return (
        item.source == "outlook_calendar"
        and item.kind == "event"
        and payload.get("type") == "occurrence"
        and bool(payload.get("seriesMasterId"))
    )


def series_units(items: list[ChangedItem]) -> list[Unit]:
    """Items must satisfy is_occurrence; the earliest occurrence of a series is rendered."""
    series: dict[tuple[int, str], list[ChangedItem]] = defaultdict(list)
    for item in items:
        series[(item.account_id, item.payload["seriesMasterId"])].append(item)
    units = [_unit(sorted(group, key=_start)) for group in series.values()]
    logger.debug("Collapsed %d occurrences into %d series units", len(items), len(units))
    return units


def _unit(occurrences: list[ChangedItem]) -> Unit:
    first, last = occurrences[0], occurrences[-1]
    unit = record_unit(first)
    heading = unit.heading.replace("Event:", "Recurring event:", 1)
    span = f"from {local_time(first.starts_at)} to {local_time(last.starts_at)}"
    body = f"{unit.body}\n- Occurrences: {len(occurrences)}, {span}"
    item_ids = [item.id for item in occurrences]
    logger.trace("Series %s: %d occurrences", first.payload["seriesMasterId"], len(item_ids))
    return replace(unit, heading=heading, body=body, item_ids=item_ids)


def _start(item: ChangedItem) -> str:
    return item.starts_at or ""

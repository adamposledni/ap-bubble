"""Reads which messages a stretch of Gmail history added, relabelled or deleted."""

from dataclasses import dataclass

from bubble_ingest.google.http import Json

_CHANGE_KINDS = ("messagesAdded", "labelsAdded", "labelsRemoved")
_DELETE_KIND = "messagesDeleted"  # deleted for good; moving to trash is a label change


@dataclass(frozen=True)
class MessageChanges:
    changed_ids: list[str]  # added or relabelled: fetch them again
    deleted_ids: list[str]


def message_changes(records: list[Json]) -> MessageChanges:
    """Distinct message ids per change, in history order; deleted ones are not fetched again."""
    deleted = _ids(records, _DELETE_KIND)
    changed = [
        message_id for message_id in _ids(records, *_CHANGE_KINDS) if message_id not in deleted
    ]
    return MessageChanges(changed, list(deleted))


def _ids(records: list[Json], *kinds: str) -> dict[str, None]:
    """Message ids in the given kinds of change, without duplicates (an ordered set)."""
    return dict.fromkeys(
        change["message"]["id"]
        for record in records
        for kind in kinds
        for change in record.get(kind, [])
    )

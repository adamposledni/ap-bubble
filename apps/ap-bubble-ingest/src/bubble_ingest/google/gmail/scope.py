"""Which messages L0 keeps: those received since SYNC_FROM, outside spam and trash."""

from datetime import datetime

from bubble_ingest.google.http import Json

SYNC_FROM = "2026-01-01T00:00:00Z"  # older mail is not loaded yet, see other/TODO.md
_SYNC_FROM_SECONDS = int(datetime.fromisoformat(SYNC_FROM).timestamp())
_EXCLUDED_LABELS = {"SPAM", "TRASH"}

# Gmail search for a full load; epoch seconds, as a plain date would be read as midnight PST.
# messages.list leaves spam and trash out by itself.
LIST_QUERY = f"after:{_SYNC_FROM_SECONDS}"


def in_scope(message: Json) -> bool:
    """False for messages a full load would not list, e.g. ones moved to trash since."""
    if _EXCLUDED_LABELS.intersection(message.get("labelIds", [])):
        return False
    return int(message["internalDate"]) >= _SYNC_FROM_SECONDS * 1000

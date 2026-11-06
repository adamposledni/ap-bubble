"""Which messages L0 keeps: those received since SYNC_FROM."""

from datetime import datetime

from bubble_ingest.microsoft.graph import Json

SYNC_FROM = "2026-01-01T00:00:00Z"  # older mail is not loaded yet, see other/TODO.md
_SYNC_FROM = datetime.fromisoformat(SYNC_FROM)

# The only $filter a messages delta supports; Graph caps a filtered first load at 5,000 messages.
RECEIVED_FILTER = f"receivedDateTime ge {SYNC_FROM}"


def in_scope(message: Json) -> bool:
    """False for messages a filtered first load would not return.

    Delta still reports read-state changes of older messages, and an unfiltered load returns them.
    """
    received = message.get("receivedDateTime")
    return received is not None and datetime.fromisoformat(received) >= _SYNC_FROM

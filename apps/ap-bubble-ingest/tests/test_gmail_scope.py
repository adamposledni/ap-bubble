import pytest

from bubble_ingest.google.gmail.scope import LIST_QUERY, in_scope

SYNC_FROM_MS = 1767225600000  # 2026-01-01T00:00:00Z


def _message(labels: list[str], internal_date: int = SYNC_FROM_MS) -> dict:
    return {"id": "m1", "labelIds": labels, "internalDate": str(internal_date)}


def test_list_query_uses_epoch_seconds() -> None:
    assert LIST_QUERY == "after:1767225600"


@pytest.mark.parametrize(
    ("labels", "internal_date", "expected"),
    [
        (["INBOX", "UNREAD"], SYNC_FROM_MS, True),
        ([], SYNC_FROM_MS + 1, True),
        (["INBOX"], SYNC_FROM_MS - 1, False),
        (["SPAM"], SYNC_FROM_MS, False),
        (["INBOX", "TRASH"], SYNC_FROM_MS, False),
    ],
)
def test_in_scope_keeps_recent_mail_outside_spam_and_trash(
    labels: list[str], internal_date: int, expected: bool
) -> None:
    assert in_scope(_message(labels, internal_date)) is expected

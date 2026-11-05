from bubble_ingest.google.gmail.history import message_changes


def _record(kind: str, *message_ids: str) -> dict:
    changes = [{"message": {"id": message_id, "threadId": "t"}} for message_id in message_ids]
    return {"id": "1", "messages": [c["message"] for c in changes], kind: changes}


def test_changes_are_distinct_ids_in_history_order() -> None:
    records = [
        _record("messagesAdded", "m1"),
        _record("labelsRemoved", "m2", "m1"),
        _record("labelsAdded", "m3"),
        _record("messagesDeleted", "m4"),
    ]

    changes = message_changes(records)

    assert (changes.changed_ids, changes.deleted_ids) == (["m1", "m2", "m3"], ["m4"])


def test_deleted_messages_are_not_fetched_again() -> None:
    records = [_record("messagesAdded", "m1"), _record("messagesDeleted", "m1")]

    changes = message_changes(records)

    assert (changes.changed_ids, changes.deleted_ids) == ([], ["m1"])


def test_no_history_means_no_changes() -> None:
    changes = message_changes([])

    assert (changes.changed_ids, changes.deleted_ids) == ([], [])

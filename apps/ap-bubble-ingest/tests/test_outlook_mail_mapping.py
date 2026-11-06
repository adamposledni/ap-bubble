from bubble_ingest.microsoft.mail.mapping import folder_to_item, is_removed, to_item
from bubble_ingest.microsoft.mail.scope import in_scope

MESSAGE = {
    "@odata.etag": 'W/"CQAAABYAAAA"',
    "id": "m1",
    "subject": "Hi",
    "receivedDateTime": "2026-03-05T10:20:30Z",
    "body": {"contentType": "text", "content": "Hello"},
    "parentFolderId": "inbox",
}


def test_message_maps_to_mail_item_of_its_folder() -> None:
    item = to_item("inbox", MESSAGE)

    assert (item.source, item.container_id, item.external_id, item.kind) == (
        "outlook_mail",
        "inbox",
        "m1",
        "mail",
    )
    assert (item.title, item.starts_at, item.ends_at) == ("Hi", "2026-03-05T10:20:30+00:00", None)
    assert not item.deleted


def test_payload_is_the_message_without_its_etag() -> None:
    payload = to_item("inbox", MESSAGE).payload

    assert payload == {key: value for key, value in MESSAGE.items() if key != "@odata.etag"}


def test_message_without_subject_or_date_has_no_title_or_start() -> None:
    item = to_item("inbox", {"id": "m1"})

    assert (item.title, item.starts_at) == (None, None)


def test_folder_maps_to_container_item() -> None:
    folder = {"id": "inbox", "displayName": "Inbox", "childFolderCount": 2}

    item = folder_to_item(folder)

    assert (item.container_id, item.external_id, item.kind, item.title) == (
        "",
        "inbox",
        "mailfolder",
        "Inbox",
    )
    assert item.payload == folder


def test_removed_entries_are_recognised() -> None:
    assert is_removed({"id": "m1", "@removed": {"reason": "deleted"}})
    assert not is_removed(MESSAGE)


def test_messages_received_before_sync_from_are_out_of_scope() -> None:
    assert in_scope({"receivedDateTime": "2026-01-01T00:00:00Z"})
    assert not in_scope({"receivedDateTime": "2025-12-31T23:59:59Z"})
    assert not in_scope({"id": "m1"})

from bubble_ingest.google.gmail.mapping import to_item


def test_message_maps_to_mail_item() -> None:
    message = {
        "id": "m1",
        "threadId": "t1",
        "labelIds": ["INBOX"],
        "internalDate": "1772705400123",
        "payload": {
            "headers": [{"name": "From", "value": "a@b.c"}, {"name": "subject", "value": "Hi"}]
        },
    }

    item = to_item(message)

    assert (item.source, item.container_id, item.external_id, item.kind) == (
        "gmail",
        "",
        "m1",
        "mail",
    )
    assert (item.title, item.starts_at, item.ends_at) == ("Hi", "2026-03-05T10:10:00+00:00", None)
    assert not item.deleted
    assert item.payload == message


def test_message_without_subject_has_no_title() -> None:
    item = to_item({"id": "m1", "internalDate": "1772705400000", "payload": {"headers": []}})

    assert item.title is None


def _with_attachment(attachment_id: str) -> dict:
    attachment = {
        "partId": "1",
        "filename": "a.pdf",
        "mimeType": "application/pdf",
        "body": {"attachmentId": attachment_id, "size": 42},
    }
    text = {"partId": "0", "mimeType": "text/plain", "body": {"size": 2, "data": "SGk="}}
    return {"id": "m1", "internalDate": "1772705400000", "payload": {"parts": [text, attachment]}}


def test_attachment_ids_are_left_out_as_gmail_changes_them_on_every_fetch() -> None:
    first, second = to_item(_with_attachment("id-1")), to_item(_with_attachment("id-2"))

    assert first.payload == second.payload
    parts = first.payload["payload"]["parts"]
    assert parts[0]["body"] == {"size": 2, "data": "SGk="}
    assert (parts[1]["partId"], parts[1]["filename"], parts[1]["body"]) == (
        "1",
        "a.pdf",
        {"size": 42},
    )

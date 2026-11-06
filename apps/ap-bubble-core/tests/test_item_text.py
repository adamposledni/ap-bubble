import base64

from bubble_core.queries.item_text import item_text


def test_graph_body_is_read_as_text() -> None:
    payload = {"body": {"contentType": "html", "content": "<p>Hi &amp; bye</p>"}}

    assert item_text("outlook_mail", payload) == "Hi & bye"


def test_gmail_text_comes_from_the_plain_part() -> None:
    data = base64.urlsafe_b64encode(b"Ahoj").decode()
    payload = {"payload": {"parts": [{"mimeType": "text/plain", "body": {"data": data}}]}}

    assert item_text("gmail", payload) == "Ahoj"


def test_plain_fields_are_used_without_a_body() -> None:
    assert item_text("google_tasks", {"notes": " Buy milk "}) == "Buy milk"
    assert item_text("google_contacts", {"names": []}) is None

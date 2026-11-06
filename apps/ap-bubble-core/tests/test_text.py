from bubble_core.text import body_text, html_to_text


def test_blocks_become_lines_and_entities_are_decoded() -> None:
    html = "<div>Hi Petr,</div><p>see you at 5&nbsp;pm &amp; bring it</p>"

    assert html_to_text(html) == "Hi Petr,\n\nsee you at 5\xa0pm & bring it"


def test_quoted_replies_are_left_out() -> None:
    html = "<p>Yes</p><blockquote><p>Shall we meet?</p></blockquote>"

    assert html_to_text(html) == "Yes"


def test_plain_bodies_are_kept_as_they_are() -> None:
    assert body_text({"contentType": "text", "content": "a <b> c"}) == "a <b> c"
    assert body_text(None) == ""

from bubble_ingest.microsoft.chats.text import SNIPPET_LENGTH, snippet


def _html(content: str) -> dict[str, str]:
    return {"contentType": "html", "content": content}


def test_html_body_becomes_one_line_of_text() -> None:
    body = _html("<div><p>Hello&nbsp;<b>world</b> &amp; all</p><p>next<br>line</p></div>")

    assert snippet(body) == "Hello world & all next line"


def test_quoted_reply_is_left_out() -> None:
    quote = '<blockquote itemtype="http://schema.skype.com/Reply"><b>Bob</b><p>Lunch?</p>'
    body = _html(f"{quote}</blockquote><p>Sure, at noon</p>")

    assert snippet(body) == "Sure, at noon"


def test_text_body_is_kept_with_whitespace_collapsed() -> None:
    assert snippet({"contentType": "text", "content": " a <b>  b\n"}) == "a <b> b"


def test_long_text_is_cut_with_an_ellipsis() -> None:
    text = snippet({"contentType": "text", "content": "word " * 40})

    assert text is not None
    assert len(text) <= SNIPPET_LENGTH
    assert text.endswith("word…")


def test_body_without_text_has_no_snippet() -> None:
    assert snippet(_html('<attachment id="a1"></attachment>')) is None
    assert snippet({"contentType": "html", "content": ""}) is None
    assert snippet(None) is None

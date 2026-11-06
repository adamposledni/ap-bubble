from pathlib import Path

import pytest

from bubble_core.paths import knowledge_dir
from bubble_core.questions import QuestionNotFound, list_questions, remove_question

CONTENT = (
    "# Open questions\n"
    "\n"
    "- Is Petr in l0:123 the same as people/petr-novak.md?\n"
    "- Which flat does input:4 refer to,\n"
    "  the one in Brno or in Prague?\n"
    "- Third question\n"
)


def _write(content: str) -> Path:
    path = knowledge_dir() / "questions.md"
    path.write_text(content, encoding="utf-8", newline="")
    return path


def test_missing_file_has_no_questions() -> None:
    assert list_questions() == []


def test_questions_are_parsed_with_wrapped_lines_joined() -> None:
    _write(CONTENT)

    texts = [q.text for q in list_questions()]

    assert texts == [
        "Is Petr in l0:123 the same as people/petr-novak.md?",
        "Which flat does input:4 refer to, the one in Brno or in Prague?",
        "Third question",
    ]


def test_id_survives_removal_of_an_earlier_question() -> None:
    _write(CONTENT)
    first, _, third = list_questions()

    remove_question(first.id)

    assert list_questions()[-1] == third


def test_removal_keeps_the_rest_of_the_file_intact() -> None:
    path = _write(CONTENT)
    _, second, _ = list_questions()

    removed = remove_question(second.id)

    assert removed == second
    assert path.read_text(encoding="utf-8") == (
        "# Open questions\n"
        "\n"
        "- Is Petr in l0:123 the same as people/petr-novak.md?\n"
        "- Third question\n"
    )


def test_removing_an_unknown_question_fails() -> None:
    _write(CONTENT)

    with pytest.raises(QuestionNotFound):
        remove_question("nope")

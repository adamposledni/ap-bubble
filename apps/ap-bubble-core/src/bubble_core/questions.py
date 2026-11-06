"""Open questions the curator leaves for me in knowledge/questions.md (one `- ` bullet each)."""

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from bubble_core.log import get_logger
from bubble_core.paths import knowledge_dir

FILE_NAME = "questions.md"
BULLET = "- "

logger = get_logger(__name__)


class QuestionNotFound(LookupError):
    pass


@dataclass(frozen=True)
class Question:
    id: str  # short hash of the normalized text, stable when other questions come and go
    text: str


@dataclass(frozen=True)
class _Span:
    """A question and the lines it occupies in the file (start inclusive, end exclusive)."""

    question: Question
    start: int
    end: int


def list_questions() -> list[Question]:
    return [span.question for span in _spans(_read_lines())]


def get_question(question_id: str) -> Question:
    for question in list_questions():
        if question.id == question_id:
            return question
    raise QuestionNotFound(f"Question {question_id} not found")


def remove_question(question_id: str) -> Question:
    """Drop the question from the file, leaving everything else intact."""
    lines = _read_lines()
    span = next((s for s in _spans(lines) if s.question.id == question_id), None)
    if span is None:
        raise QuestionNotFound(f"Question {question_id} not found")
    _write_lines(lines[: span.start] + lines[span.end :])
    logger.info("Removed question %s", question_id)
    return span.question


def _spans(lines: list[str]) -> list[_Span]:
    spans: list[_Span] = []
    for index, line in enumerate(lines):
        if line.startswith(BULLET):
            spans.append(_Span(Question("", ""), index, index + 1))
        elif spans and line[:1] in (" ", "\t") and line.strip():
            spans[-1] = _Span(spans[-1].question, spans[-1].start, index + 1)
    return [_with_question(span, lines) for span in spans]


def _with_question(span: _Span, lines: list[str]) -> _Span:
    text = _normalize(" ".join(lines[span.start : span.end])[len(BULLET) :])
    return _Span(Question(_make_id(text), text), span.start, span.end)


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _make_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def _path() -> Path:
    return knowledge_dir() / FILE_NAME


def _read_lines() -> list[str]:
    path = _path()
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def _write_lines(lines: list[str]) -> None:
    path = _path()
    temp = path.with_suffix(".md.tmp")
    temp.write_text("".join(lines), encoding="utf-8", newline="")
    os.replace(temp, path)

"""Curator questions waiting for me: list, answer (becomes an L1 input) or dismiss."""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from bubble_api.deps import Conn
from bubble_api.models import InputOut, QuestionOut
from bubble_core.inputs import add_input
from bubble_core.log import get_logger
from bubble_core.questions import (
    Question,
    QuestionNotFound,
    get_question,
    list_questions,
    remove_question,
)

router = APIRouter(prefix="/questions")
logger = get_logger(__name__)


class AnswerIn(BaseModel):
    text: str


@router.get("")
def get_questions() -> list[QuestionOut]:
    return [QuestionOut.model_validate(question) for question in list_questions()]


@router.post("/{question_id}/answer", status_code=201)
def answer_question(conn: Conn, question_id: str, answer: AnswerIn) -> InputOut:
    question = _find(question_id)
    if not answer.text.strip():
        raise HTTPException(422, "The answer is empty")
    text = f'Answer to the curator\'s question "{question.text}":\n\n{answer.text.strip()}'
    created = add_input(conn, text, [])
    remove_question(question_id)
    logger.info("Answered question %s with input %d", question_id, created.id)
    return InputOut.model_validate(created)


@router.post("/{question_id}/dismiss", status_code=204)
def dismiss_question(question_id: str) -> Response:
    _find(question_id)
    remove_question(question_id)
    logger.info("Dismissed question %s", question_id)
    return Response(status_code=204)


def _find(question_id: str) -> Question:
    try:
        return get_question(question_id)
    except QuestionNotFound as error:
        raise HTTPException(404, str(error)) from error

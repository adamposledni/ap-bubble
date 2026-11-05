"""Overview: the agenda of all calendars and the open tasks (L0, until curation exists)."""

from datetime import date
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException, Query

from bubble_api.deps import Conn
from bubble_api.models import AgendaEventOut, OpenTaskOut
from bubble_core.queries.agenda import agenda
from bubble_core.queries.tasks import open_tasks

_MAX_DAYS = 31

router = APIRouter()


@router.get("/agenda")
def get_agenda(
    conn: Conn,
    start: date,
    tz: str,
    days: Annotated[int, Query(ge=1, le=_MAX_DAYS)] = 7,
) -> list[AgendaEventOut]:
    """Events from start (a day in tz) for the given number of days."""
    events = agenda(conn, start, days, _zone(tz))
    return [AgendaEventOut.model_validate(event) for event in events]


@router.get("/tasks")
def get_tasks(conn: Conn) -> list[OpenTaskOut]:
    return [OpenTaskOut.model_validate(task) for task in open_tasks(conn)]


def _zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise HTTPException(422, f"Unknown time zone: {name}") from error

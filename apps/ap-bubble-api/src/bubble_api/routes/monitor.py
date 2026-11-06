"""Monitoring: job health per source and account, recent runs, the input queue."""

from fastapi import APIRouter

from bubble_api.deps import Conn
from bubble_api.models import MonitorOut
from bubble_core.queries.monitor import monitor

router = APIRouter()


@router.get("/monitor")
def get_monitor(conn: Conn) -> MonitorOut:
    return MonitorOut.model_validate(monitor(conn))

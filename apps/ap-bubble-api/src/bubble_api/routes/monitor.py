"""Monitoring: job health, runs (with the curator's batches), the input queue."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from bubble_api.deps import Conn
from bubble_api.models import MonitorOut, RunDetailOut
from bubble_core.curator_runs import batch_text
from bubble_core.queries.job_runs import run_detail
from bubble_core.queries.monitor import monitor

router = APIRouter()


@router.get("/monitor")
def get_monitor(conn: Conn) -> MonitorOut:
    return MonitorOut.model_validate(monitor(conn))


@router.get("/monitor/runs/{run_id}")
def get_run(run_id: int, conn: Conn) -> RunDetailOut:
    detail = run_detail(conn, run_id)
    if detail is None:
        raise HTTPException(404, "Run not found")
    return RunDetailOut.model_validate(detail)


@router.get("/monitor/runs/{run_id}/batches/{name}", response_class=PlainTextResponse)
def get_batch(run_id: int, name: str) -> str:
    text = batch_text(run_id, name)
    if text is None:
        raise HTTPException(404, "Batch not found")
    return text

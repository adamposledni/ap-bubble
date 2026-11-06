"""The FastAPI application: brings the vault schema up to date, then serves /api."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from bubble_api.routes import inputs, monitor, overview
from bubble_core.db import migrate
from bubble_core.log import get_logger

API_PREFIX = "/api"

logger = get_logger(__name__)


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    version = migrate()
    logger.info("Vault schema at version %d; API ready", version)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="ap-bubble", lifespan=_lifespan)
    app.include_router(overview.router, prefix=API_PREFIX)
    app.include_router(inputs.router, prefix=API_PREFIX)
    app.include_router(monitor.router, prefix=API_PREFIX)
    return app

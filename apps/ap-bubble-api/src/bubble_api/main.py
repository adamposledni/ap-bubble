"""Runs the API on localhost only; the web app's dev server proxies /api to it."""

import uvicorn

from bubble_api.app import create_app
from bubble_core.log import setup_logging

APP_NAME = "ap-bubble-api"
HOST = "127.0.0.1"
PORT = 8787


def main() -> None:
    setup_logging(APP_NAME)
    uvicorn.run(create_app(), host=HOST, port=PORT, log_config=None)

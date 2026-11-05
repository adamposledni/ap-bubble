"""Locations of runtime data, kept outside the repo."""

import os
from pathlib import Path

APP_NAME = "ap-bubble"
DATA_DIR_ENV = "BUBBLE_DATA_DIR"


def data_dir() -> Path:
    """Root of runtime data: the env override if set, else %LOCALAPPDATA%/ap-bubble."""
    override = os.environ.get(DATA_DIR_ENV)
    return _ensure(Path(override) if override else _local_app_data() / APP_NAME)


def db_path() -> Path:
    return data_dir() / "vault.db"


def logs_dir() -> Path:
    return _ensure(data_dir() / "logs")


def _local_app_data() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

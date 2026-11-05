"""Logging shared by all components, with an extra TRACE level below DEBUG."""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any, cast

from adams_bubble_core.paths import logs_dir

TRACE = 5
LOG_LEVEL_ENV = "ADAMS_BUBBLE_LOG_LEVEL"
_FORMAT = "%(asctime)s %(levelname)-5s %(name)s: %(message)s"
_MAX_FILE_BYTES = 5 * 1024 * 1024
_BACKUP_FILES = 5


class TraceLogger(logging.Logger):
    def trace(self, msg: object, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(TRACE):
            self._log(TRACE, msg, args, **kwargs)


logging.addLevelName(TRACE, "TRACE")
logging.setLoggerClass(TraceLogger)


def get_logger(name: str) -> TraceLogger:
    return cast(TraceLogger, logging.getLogger(name))


def setup_logging(app_name: str) -> None:
    """Log to the console and to a rotating file <logs>/<app_name>.log.

    The level comes from ADAMS_BUBBLE_LOG_LEVEL (TRACE, DEBUG, INFO, ...), default INFO.
    """
    formatter = logging.Formatter(_FORMAT)
    handlers: list[logging.Handler] = [logging.StreamHandler(), _file_handler(app_name)]
    for handler in handlers:
        handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = handlers
    root.setLevel(os.environ.get(LOG_LEVEL_ENV, "INFO").upper())


def _file_handler(app_name: str) -> RotatingFileHandler:
    return RotatingFileHandler(
        logs_dir() / f"{app_name}.log",
        maxBytes=_MAX_FILE_BYTES,
        backupCount=_BACKUP_FILES,
        encoding="utf-8",
    )

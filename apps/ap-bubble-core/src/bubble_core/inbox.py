"""Files of L1 inputs in the inbox folder, laid out as <inbox>/<input id>/<n>_<safe name>."""

import re
import shutil
from pathlib import Path
from typing import BinaryIO

from bubble_core.log import get_logger
from bubble_core.paths import inbox_dir

_UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_MAX_NAME_LENGTH = 100

logger = get_logger(__name__)


def store_file(input_id: int, index: int, file_name: str, content: BinaryIO) -> tuple[str, int]:
    """Copy the content into the input's folder; return its inbox-relative path and size."""
    relative = f"{input_id}/{index}_{safe_name(file_name)}"
    target = inbox_dir() / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as out:
        shutil.copyfileobj(content, out)
    size = target.stat().st_size
    logger.debug("Stored inbox file %s (%d bytes)", relative, size)
    return relative, size


def path_of(relative: str) -> Path:
    return inbox_dir() / relative


def remove_files(input_id: int) -> None:
    shutil.rmtree(inbox_dir() / str(input_id), ignore_errors=True)
    logger.debug("Removed inbox files of input %d", input_id)


def safe_name(file_name: str) -> str:
    """The file name without any folder part or characters Windows does not allow."""
    name = _UNSAFE_CHARS.sub("_", Path(file_name).name).strip(" .")
    return (name or "file")[-_MAX_NAME_LENGTH:]

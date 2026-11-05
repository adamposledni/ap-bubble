"""Request dependencies: one vault connection per request."""

import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends

from bubble_core.db import connect


def get_conn() -> Iterator[sqlite3.Connection]:
    conn = connect(check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


Conn = Annotated[sqlite3.Connection, Depends(get_conn)]

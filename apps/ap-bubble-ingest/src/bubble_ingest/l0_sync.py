"""Steps shared by L0 ingest jobs: a run per account, cursor-based sync of one container."""

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

from bubble_core.accounts import Account, Provider, list_accounts
from bubble_core.items import Item, flag_missing_deleted, save_item
from bubble_core.job_log import JobRun
from bubble_core.log import get_logger
from bubble_core.sync_cursors import load_cursor, save_cursor

CONTAINER_LIST_ID = ""  # container of the items that describe a source's containers

logger = get_logger(__name__)


class CursorExpired(Exception):
    """The source no longer accepts the stored cursor; the container needs a full load."""


@dataclass(frozen=True)
class ContainerChanges:
    """What one fetch from a container returned: changed items (or all, on a full load)."""

    items: list[Item]
    next_cursor: str
    full_load: bool


# Gets changes since the cursor, or everything when the cursor is None; may raise CursorExpired.
type Fetch = Callable[[str | None], ContainerChanges]


def sync_accounts(
    conn: sqlite3.Connection,
    provider: Provider,
    sync_account: Callable[[sqlite3.Connection, Account], None],
) -> None:
    """Run sync_account for every enabled account; a failed account does not stop the others."""
    failed = []
    for account in list_accounts(conn, provider):
        try:
            sync_account(conn, account)
        except Exception:  # already logged and recorded by job_run
            failed.append(account.key)
    if failed:
        raise RuntimeError(f"Sync failed for {failed}")


def save_containers(
    conn: sqlite3.Connection, account: Account, source: str, containers: list[Item], run: JobRun
) -> None:
    """Save the containers themselves (calendars, task lists); flag removed ones; commit."""
    changed = sum(save_item(conn, account.id, item, run.id) for item in containers)
    seen = {item.external_id for item in containers}
    changed += flag_missing_deleted(conn, account.id, source, CONTAINER_LIST_ID, seen, run.id)
    conn.commit()
    logger.debug("%s: %d containers, %d changed", source, len(containers), changed)


def sync_container(
    conn: sqlite3.Connection,
    account: Account,
    source: str,
    container_id: str,
    fetch: Fetch,
    run: JobRun,
) -> None:
    """Fetch changes since the stored cursor (a full load when none or expired) and apply them."""
    changes = _fetch(conn, account, source, container_id, fetch)
    apply_changes(conn, account, source, container_id, changes, run)


def apply_changes(
    conn: sqlite3.Connection,
    account: Account,
    source: str,
    container_id: str,
    changes: ContainerChanges,
    run: JobRun,
) -> None:
    """Save the items, flag missing ones after a full load, store the cursor; commit together."""
    changed = sum(save_item(conn, account.id, item, run.id) for item in changes.items)
    if changes.full_load:
        seen = {item.external_id for item in changes.items}
        changed += flag_missing_deleted(conn, account.id, source, container_id, seen, run.id)
    save_cursor(conn, account.id, source, container_id, changes.next_cursor)
    conn.commit()
    run.items_processed += len(changes.items)
    logger.info(
        "%s %s: %d items fetched, %d changed (%s)",
        source,
        container_id or "-",
        len(changes.items),
        changed,
        "full load" if changes.full_load else "incremental",
    )


def _fetch(
    conn: sqlite3.Connection, account: Account, source: str, container_id: str, fetch: Fetch
) -> ContainerChanges:
    cursor = load_cursor(conn, account.id, source, container_id)
    if cursor:
        try:
            return fetch(cursor)
        except CursorExpired:
            logger.warning("Cursor of %s %s expired; loading it fully", source, container_id)
    return fetch(None)

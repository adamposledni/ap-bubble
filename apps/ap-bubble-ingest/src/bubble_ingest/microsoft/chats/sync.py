"""Ingest job: syncs the Teams chats of every Microsoft account into L0, one container per chat.

Each chat keeps its own cursor: the newest lastModifiedDateTime seen in it. A fetch asks for the
messages modified after the cursor (after SYNC_FROM on a chat's first load); edits, reactions and
soft deletions change lastModifiedDateTime, so they arrive as changed messages.

Chats are listed by their last message, latest first, and the listing stops at the first chat
whose last message predates SYNC_FROM: only chats active since then are containers. A chat whose
last message is not newer than its cursor is skipped without a call; the chat's
lastUpdatedDateTime would not do, as it changes only on renames and member changes. So a change
to an older message is picked up with the next new message in its chat (see other/TODO.md).

Graph lists some chats whose messages it does not let the user read (403), e.g. ones of chat
types v1.0 does not name yet. Such a chat counts as having no messages, so its cursor still moves
to its last message and it is tried again only when a new message arrives.
"""

import sqlite3
from datetime import datetime
from http import HTTPStatus

import requests

from bubble_core.accounts import Account
from bubble_core.job_log import JobRun, job_run
from bubble_core.log import get_logger
from bubble_core.sync_cursors import load_cursor
from bubble_ingest.l0_sync import ContainerChanges, apply_changes, save_containers, sync_accounts
from bubble_ingest.microsoft import auth as microsoft_auth
from bubble_ingest.microsoft.chats import api
from bubble_ingest.microsoft.chats.mapping import SOURCE, chat_to_item, to_item
from bubble_ingest.microsoft.graph import Json

JOB_NAME = f"ingest.{SOURCE}"
SYNC_FROM = "2026-01-01T00:00:00Z"  # older messages are not loaded yet, see other/TODO.md

logger = get_logger(__name__)


def sync_all(conn: sqlite3.Connection) -> None:
    sync_accounts(conn, "microsoft", sync_account)


def sync_account(conn: sqlite3.Connection, account: Account) -> None:
    with job_run(conn, JOB_NAME, account.key) as run:
        session = microsoft_auth.session_for(account.key)
        chats = _active_chats(session)
        my_user_id = api.my_user_id(session)
        save_containers(conn, account, SOURCE, [chat_to_item(c, my_user_id) for c in chats], run)
        synced = sum(_sync_chat(conn, account, session, chat, run) for chat in chats)
        logger.info(
            "Teams chats of %s: %d active since %s, %d with new messages",
            account.key,
            len(chats),
            SYNC_FROM,
            synced,
        )


def _active_chats(session: requests.Session) -> list[Json]:
    """Chats with a message since SYNC_FROM; stops listing at the first older chat."""
    active = []
    for chat in api.iter_chats_by_last_message(session):
        if not chat.get("lastMessagePreview"):
            continue  # no messages, nothing to load
        if _time(_last_message_at(chat)) <= _time(SYNC_FROM):
            break
        active.append(chat)
    logger.debug("%d chats active since %s", len(active), SYNC_FROM)
    return active


def _sync_chat(
    conn: sqlite3.Connection, account: Account, session: requests.Session, chat: Json, run: JobRun
) -> bool:
    """Load the chat's messages changed since its cursor; False when it had nothing new."""
    cursor = load_cursor(conn, account.id, SOURCE, chat["id"])
    if cursor and _time(_last_message_at(chat)) <= _time(cursor):
        logger.trace("Chat %s has no new messages", chat["id"])
        return False
    changes = _fetch_changes(session, chat, cursor)
    apply_changes(conn, account, SOURCE, chat["id"], changes, run)
    return True


def _fetch_changes(session: requests.Session, chat: Json, cursor: str | None) -> ContainerChanges:
    since = cursor or SYNC_FROM
    messages = _readable_messages(session, chat["id"], since)
    in_scope = [m for m in messages if _time(m["createdDateTime"]) >= _time(SYNC_FROM)]
    logger.trace("Chat %s: %d of %d messages in scope", chat["id"], len(in_scope), len(messages))
    # At least the last message's time, so a chat whose list lacks it is not fetched every run.
    modified = [m["lastModifiedDateTime"] for m in messages]
    next_cursor = max([since, _last_message_at(chat), *modified], key=_time)
    items = [to_item(chat["id"], message) for message in in_scope]
    return ContainerChanges(items, next_cursor, full_load=cursor is None)


def _readable_messages(session: requests.Session, chat_id: str, since: str) -> list[Json]:
    """The chat's messages changed since `since`; none when Graph forbids reading them."""
    try:
        return api.list_messages(session, chat_id, since)
    except requests.HTTPError as error:
        if error.response is None or error.response.status_code != HTTPStatus.FORBIDDEN:
            raise
    logger.warning("Reading messages of chat %s is forbidden; skipped until a new one", chat_id)
    return []


def _last_message_at(chat: Json) -> str:
    """When the chat's last message was sent; only for chats that have messages."""
    return chat["lastMessagePreview"]["createdDateTime"]


def _time(timestamp: str) -> datetime:
    """Graph's timestamps vary in fractional digits, so they are compared as datetimes."""
    return datetime.fromisoformat(timestamp)

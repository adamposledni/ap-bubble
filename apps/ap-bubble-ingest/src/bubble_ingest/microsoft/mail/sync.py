"""Ingest job: syncs the mail of every Microsoft account into L0, one container per mail folder.

Folders are listed on every run (see folders.py) and saved as containers. Each folder is then
synced through its own messages delta (see folder_sync.py); moves and removals in store.py.
"""

import sqlite3

from bubble_core.accounts import Account
from bubble_core.job_log import job_run
from bubble_core.log import get_logger
from bubble_ingest.l0_sync import save_containers, sync_accounts
from bubble_ingest.microsoft import auth as microsoft_auth
from bubble_ingest.microsoft.mail.folder_sync import sync_folder
from bubble_ingest.microsoft.mail.folders import synced_folders
from bubble_ingest.microsoft.mail.mapping import SOURCE, folder_to_item
from bubble_ingest.microsoft.mail.store import Mailbox, retire_vanished_folders

JOB_NAME = f"ingest.{SOURCE}"

logger = get_logger(__name__)


def sync_all(conn: sqlite3.Connection) -> None:
    sync_accounts(conn, "microsoft", sync_account)


def sync_account(conn: sqlite3.Connection, account: Account) -> None:
    with job_run(conn, JOB_NAME, account.key) as run:
        mailbox = Mailbox(conn, microsoft_auth.session_for(account.key), account, run)
        folders = synced_folders(mailbox.session)
        save_containers(conn, account, SOURCE, [folder_to_item(f) for f in folders], run)
        retire_vanished_folders(mailbox, {folder["id"] for folder in folders})
        for folder in folders:
            sync_folder(mailbox, folder["id"])
        logger.debug("Synced %d mail folders of %s", len(folders), account.key)

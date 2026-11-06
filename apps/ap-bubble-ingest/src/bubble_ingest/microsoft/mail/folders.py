"""Which mail folders are synced: every folder and subfolder, except system and search folders.

A skipped folder is skipped with all its subfolders.
"""

import requests

from bubble_core.log import get_logger
from bubble_ingest.microsoft.graph import Json
from bubble_ingest.microsoft.mail import api

# Graph v1.0 well-known names of the skipped folders (they work in any mailbox language).
SKIPPED_FOLDERS = (
    "deleteditems",  # deleting moves a message here; it then counts as removed from its folder
    "junkemail",
    "drafts",
    "outbox",
    "conversationhistory",  # Skype / Teams conversation copies
    "syncissues",  # Outlook sync logs, with Conflicts, Local Failures and Server Failures below
    "recoverableitemsdeletions",  # outside the listed tree anyway; skipped should it show up
)
# Virtual folders whose messages live in other folders; syncing them would duplicate those.
_SEARCH_FOLDER_TYPE = "#microsoft.graph.mailSearchFolder"

logger = get_logger(__name__)


def synced_folders(session: requests.Session) -> list[Json]:
    skipped = _skipped_ids(session)
    folders: list[Json] = []
    _collect(session, None, skipped, folders)
    logger.debug("%d mail folders to sync", len(folders))
    return folders


def _skipped_ids(session: requests.Session) -> set[str]:
    ids = {api.well_known_folder_id(session, name) for name in SKIPPED_FOLDERS}
    return {folder_id for folder_id in ids if folder_id}


def _collect(
    session: requests.Session, parent_id: str | None, skipped: set[str], found: list[Json]
) -> None:
    """Add the synced folders under parent_id, depth first."""
    for folder in api.list_folders(session, parent_id):
        if folder["id"] in skipped or folder.get("@odata.type") == _SEARCH_FOLDER_TYPE:
            logger.trace("Skipping folder %s and its subfolders", folder["id"])
            continue
        found.append(folder)
        if folder.get("childFolderCount"):
            _collect(session, folder["id"], skipped, found)

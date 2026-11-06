from typing import Any

import pytest

from bubble_ingest.microsoft.mail import api
from bubble_ingest.microsoft.mail.folders import synced_folders

WELL_KNOWN = {"deleteditems": "deleted", "syncissues": "sync", "junkemail": "junk"}
SEARCH_FOLDER = "#microsoft.graph.mailSearchFolder"
TREE: dict[str | None, list[dict[str, Any]]] = {
    None: [
        {"id": "inbox", "childFolderCount": 1},
        {"id": "deleted", "childFolderCount": 1},
        {"id": "sync", "childFolderCount": 1},
        {"id": "junk", "childFolderCount": 0},
        {"id": "digests", "childFolderCount": 0, "@odata.type": SEARCH_FOLDER},
        {"id": "archive", "childFolderCount": 0},
    ],
    "inbox": [{"id": "projects", "childFolderCount": 1}],
    "projects": [{"id": "deep", "childFolderCount": 0}],
    "deleted": [{"id": "deleted-folder", "childFolderCount": 0}],
    "sync": [{"id": "conflicts", "childFolderCount": 0}],
}


@pytest.fixture
def listed(monkeypatch: pytest.MonkeyPatch) -> list[str | None]:
    """Parents whose folders were listed."""
    parents: list[str | None] = []

    def list_folders(session: object, parent_id: str | None) -> list[dict[str, Any]]:
        parents.append(parent_id)
        return TREE[parent_id]

    monkeypatch.setattr(api, "well_known_folder_id", lambda session, name: WELL_KNOWN.get(name))
    monkeypatch.setattr(api, "list_folders", list_folders)
    return parents


def test_all_folders_are_synced_depth_first_except_skipped_ones(listed: list[str | None]) -> None:
    folders = synced_folders(object())  # type: ignore[arg-type]

    assert [folder["id"] for folder in folders] == ["inbox", "projects", "deep", "archive"]


def test_subfolders_of_skipped_folders_are_not_listed(listed: list[str | None]) -> None:
    synced_folders(object())  # type: ignore[arg-type]

    assert listed == [None, "inbox", "projects"]

from contextlib import closing
from pathlib import Path

from ap_adams_bubble_core.db import connect, migrate


def test_migrate_creates_schema_and_sets_version(vault_path: Path) -> None:
    version = migrate(vault_path)

    with closing(connect(vault_path)) as conn:
        tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master")}
        stored_version = conn.execute("PRAGMA user_version").fetchone()[0]

    assert version >= 1
    assert stored_version == version
    assert "job_runs" in tables


def test_migrate_twice_is_a_no_op(vault_path: Path) -> None:
    assert migrate(vault_path) == migrate(vault_path)

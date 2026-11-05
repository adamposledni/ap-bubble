from pathlib import Path

import pytest


@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    return tmp_path / "vault.db"

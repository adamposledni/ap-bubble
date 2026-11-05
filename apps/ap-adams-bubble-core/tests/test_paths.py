from pathlib import Path

import pytest

from adams_bubble_core import paths


def test_data_dir_honours_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(paths.DATA_DIR_ENV, str(tmp_path / "data"))

    assert paths.data_dir() == tmp_path / "data"
    assert paths.data_dir().is_dir()

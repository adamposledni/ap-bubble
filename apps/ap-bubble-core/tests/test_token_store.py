import keyring
import pytest

from bubble_core import token_store
from bubble_core.token_store import MAX_PART_LENGTH, load_refresh_token, save_refresh_token


@pytest.fixture(autouse=True)
def vault(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """An in-memory stand-in for Credential Manager, so tests never touch the real one."""
    entries: dict[str, str] = {}
    monkeypatch.setattr(keyring, "set_password", lambda s, k, v: entries.__setitem__(k, v))
    monkeypatch.setattr(keyring, "get_password", lambda s, k: entries.get(k))
    monkeypatch.setattr(keyring, "delete_password", lambda s, k: entries.pop(k))
    return entries


def test_short_token_uses_one_entry(vault: dict[str, str]) -> None:
    save_refresh_token("google:me", "short")

    assert vault == {"google:me": "short"}
    assert load_refresh_token("google:me") == "short"


def test_long_token_is_split_and_joined(vault: dict[str, str]) -> None:
    token = "x" * (2 * MAX_PART_LENGTH + 5)

    save_refresh_token("microsoft:me", token)

    assert set(vault) == {"microsoft:me", "microsoft:me#2", "microsoft:me#3"}
    assert max(len(part) for part in vault.values()) == MAX_PART_LENGTH
    assert load_refresh_token("microsoft:me") == token


def test_shorter_token_removes_leftover_parts(vault: dict[str, str]) -> None:
    save_refresh_token("microsoft:me", "x" * (MAX_PART_LENGTH + 1))

    save_refresh_token("microsoft:me", "new")

    assert vault == {"microsoft:me": "new"}


def test_missing_token_raises() -> None:
    with pytest.raises(LookupError):
        token_store.load_refresh_token("nobody")

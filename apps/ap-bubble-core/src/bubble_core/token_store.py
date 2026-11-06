"""Refresh tokens of connected accounts, kept in Windows Credential Manager (via keyring).

Credential Manager holds at most 1280 characters per entry, and Microsoft refresh tokens can be
longer, so a token is split: the first part under the account key, the rest under
'<account key>#2', '#3', ...
"""

import keyring

from bubble_core.log import get_logger

SERVICE_NAME = "ap-bubble"
MAX_PART_LENGTH = 1280  # Credential Manager's limit per entry

logger = get_logger(__name__)


def save_refresh_token(account_key: str, token: str) -> None:
    parts = [token[i : i + MAX_PART_LENGTH] for i in range(0, len(token), MAX_PART_LENGTH)]
    for index, part in enumerate(parts or [""], start=1):
        keyring.set_password(SERVICE_NAME, _entry(account_key, index), part)
    _delete_parts_from(account_key, len(parts) + 1)
    logger.debug("Stored refresh token for %s (%d parts)", account_key, len(parts))


def load_refresh_token(account_key: str) -> str:
    parts: list[str] = []
    while (
        part := keyring.get_password(SERVICE_NAME, _entry(account_key, len(parts) + 1))
    ) is not None:
        parts.append(part)
    if not parts:
        raise LookupError(f"No stored token for {account_key}; connect the account again")
    logger.trace("Loaded refresh token for %s (%d parts)", account_key, len(parts))
    return "".join(parts)


def _delete_parts_from(account_key: str, index: int) -> None:
    """Remove parts left over from an earlier, longer token."""
    while keyring.get_password(SERVICE_NAME, _entry(account_key, index)) is not None:
        keyring.delete_password(SERVICE_NAME, _entry(account_key, index))
        index += 1


def _entry(account_key: str, index: int) -> str:
    return account_key if index == 1 else f"{account_key}#{index}"

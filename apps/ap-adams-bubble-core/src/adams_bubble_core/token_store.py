"""Refresh tokens of connected accounts, kept in Windows Credential Manager (via keyring)."""

import keyring

from adams_bubble_core.log import get_logger

SERVICE_NAME = "ap-adams-bubble"

logger = get_logger(__name__)


def save_refresh_token(account_key: str, token: str) -> None:
    keyring.set_password(SERVICE_NAME, account_key, token)
    logger.debug("Stored refresh token for %s", account_key)


def load_refresh_token(account_key: str) -> str:
    token = keyring.get_password(SERVICE_NAME, account_key)
    if token is None:
        raise LookupError(f"No stored token for {account_key}; connect the account again")
    logger.trace("Loaded refresh token for %s", account_key)
    return token

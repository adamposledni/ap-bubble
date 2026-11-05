"""Google OAuth: browser login for connecting an account (read-only scopes)."""

import os
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from bubble_core.log import get_logger
from bubble_core.paths import data_dir

CLIENT_FILE_NAME = "google-client.json"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/tasks.readonly",
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/contacts.other.readonly",
]
_HTTP_TIMEOUT_SECONDS = 30

logger = get_logger(__name__)


def login() -> tuple[str, Credentials]:
    """Run the browser consent flow; return the account's email and its credentials."""
    # Google lets the user untick scopes; we check them ourselves instead of oauthlib raising.
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
    flow = InstalledAppFlow.from_client_secrets_file(str(client_file()), SCOPES)
    credentials = flow.run_local_server(port=0, prompt="consent")
    _validate(credentials)
    email = _email_of(credentials)
    logger.info("Google login succeeded for %s", email)
    return email, credentials


def client_file() -> Path:
    path = data_dir() / CLIENT_FILE_NAME
    if not path.exists():
        raise FileNotFoundError(f"Google OAuth client file not found: {path}")
    return path


def _validate(credentials: Credentials) -> None:
    granted = credentials.granted_scopes or []
    granted_set = set(granted.split() if isinstance(granted, str) else granted)
    missing = sorted(set(SCOPES) - granted_set)
    if missing:
        raise PermissionError(f"Permissions not granted: {missing}. Connect again, tick all boxes.")
    if not credentials.refresh_token:
        raise PermissionError("Google returned no refresh token. Connect the account again.")


def _email_of(credentials: Credentials) -> str:
    response = AuthorizedSession(credentials).get(USERINFO_URL, timeout=_HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()["email"]

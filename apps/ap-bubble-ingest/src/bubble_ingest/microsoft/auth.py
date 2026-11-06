"""Microsoft login (MSAL, public client) to connect an account, and Graph sessions for it.

Microsoft rotates refresh tokens, so every session start stores the new one it receives.
"""

import json
from pathlib import Path
from typing import Any

import msal
import requests

from bubble_core.log import get_logger
from bubble_core.paths import data_dir
from bubble_core.token_store import load_refresh_token, save_refresh_token

CLIENT_FILE_NAME = "microsoft-client.json"  # {"client_id": ..., "tenant_id": ...}
# Delegated, read-only; MSAL adds openid, profile and offline_access itself.
SCOPES = ["User.Read", "Mail.Read", "Calendars.Read", "Tasks.Read", "Chat.Read", "Notes.Read"]
_GRAPH_SCOPE_PREFIX = "https://graph.microsoft.com/"

logger = get_logger(__name__)


def login() -> tuple[str, str]:
    """Run the browser sign-in; return the account's email and its refresh token."""
    result = _app().acquire_token_interactive(scopes=SCOPES, prompt="select_account")
    _validate(result)
    email = result["id_token_claims"]["preferred_username"]
    logger.info("Microsoft login succeeded for %s", email)
    return email, result["refresh_token"]


def session_for(account_key: str) -> requests.Session:
    """HTTP session for Graph as the connected account; access tokens refresh as needed."""
    app = _app()
    result = app.acquire_token_by_refresh_token(load_refresh_token(account_key), scopes=SCOPES)
    _validate(result)
    save_refresh_token(account_key, result["refresh_token"])
    session = requests.Session()
    session.auth = _GraphAuth(app, app.get_accounts()[0])
    logger.debug("Graph session ready for %s", account_key)
    return session


def missing_scopes(granted: str) -> list[str]:
    """Our scopes absent from a token response's space-separated 'scope' value."""
    names = {scope.removeprefix(_GRAPH_SCOPE_PREFIX).lower() for scope in granted.split()}
    return [scope for scope in SCOPES if scope.lower() not in names]


class _GraphAuth(requests.auth.AuthBase):
    """Adds a current access token to every request (MSAL refreshes it from its cache)."""

    def __init__(self, app: msal.PublicClientApplication, account: dict[str, Any]) -> None:
        self._app = app
        self._account = account

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        result = self._app.acquire_token_silent(SCOPES, account=self._account)
        if not result or "access_token" not in result:
            raise PermissionError("Could not refresh the Microsoft access token; connect again")
        request.headers["Authorization"] = f"Bearer {result['access_token']}"
        return request


def _validate(result: dict[str, Any]) -> None:
    if "error" in result:
        raise PermissionError(f"Microsoft sign-in failed: {result.get('error_description')}")
    missing = missing_scopes(result.get("scope", ""))
    if missing:
        raise PermissionError(f"Permissions not granted: {missing}; an admin may need to consent")
    if not result.get("refresh_token"):
        raise PermissionError("Microsoft returned no refresh token; connect the account again")


def _app() -> msal.PublicClientApplication:
    client = json.loads(client_file().read_text(encoding="utf-8"))
    authority = f"https://login.microsoftonline.com/{client['tenant_id']}"
    return msal.PublicClientApplication(client["client_id"], authority=authority)


def client_file() -> Path:
    path = data_dir() / CLIENT_FILE_NAME
    if not path.exists():
        raise FileNotFoundError(f"Microsoft client file not found: {path}")
    return path

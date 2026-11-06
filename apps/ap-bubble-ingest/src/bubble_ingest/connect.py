"""Connecting data-source accounts: log in, store the refresh token, register the account."""

from contextlib import closing

from bubble_core.accounts import Account, Context, Provider, account_key, upsert_account
from bubble_core.db import open_vault
from bubble_core.log import get_logger
from bubble_core.token_store import save_refresh_token
from bubble_ingest.google import auth as google_auth
from bubble_ingest.microsoft import auth as microsoft_auth

logger = get_logger(__name__)


def connect_google(context: Context) -> Account:
    email, credentials = google_auth.login()
    return _register("google", email, credentials.refresh_token, context)


def connect_microsoft(context: Context) -> Account:
    email, refresh_token = microsoft_auth.login()
    return _register("microsoft", email, refresh_token, context)


def _register(provider: Provider, email: str, refresh_token: str, context: Context) -> Account:
    save_refresh_token(account_key(provider, email), refresh_token)
    with closing(open_vault()) as conn:
        account = upsert_account(conn, provider, email, context)
    logger.info("Connected %s as %s", account.key, account.context)
    return account

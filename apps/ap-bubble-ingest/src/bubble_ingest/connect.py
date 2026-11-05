"""Connecting data-source accounts: log in, store the refresh token, register the account."""

from contextlib import closing

from bubble_core.accounts import Account, Context, account_key, upsert_account
from bubble_core.db import open_vault
from bubble_core.log import get_logger
from bubble_core.token_store import save_refresh_token
from bubble_ingest.google import auth as google_auth

logger = get_logger(__name__)


def connect_google(context: Context) -> Account:
    email, credentials = google_auth.login()
    save_refresh_token(account_key("google", email), credentials.refresh_token)
    with closing(open_vault()) as conn:
        account = upsert_account(conn, "google", email, context)
    logger.info("Connected %s as %s", account.key, account.context)
    return account

"""Connected data-source accounts (lm_accounts); never the app's own identity."""

import sqlite3
from dataclasses import dataclass
from typing import Literal, cast, get_args

from adams_bubble_core.clock import utc_now
from adams_bubble_core.log import get_logger

Provider = Literal["google", "microsoft"]
Context = Literal["work", "personal"]
CONTEXTS: tuple[str, ...] = get_args(Context)

logger = get_logger(__name__)


@dataclass(frozen=True)
class Account:
    id: int
    provider: Provider
    email: str
    context: Context
    enabled: bool

    @property
    def key(self) -> str:
        return account_key(self.provider, self.email)


def account_key(provider: Provider, email: str) -> str:
    """Stable account key, e.g. 'google:me@gmail.com'; also names its token store entry."""
    return f"{provider}:{email.lower()}"


def upsert_account(
    conn: sqlite3.Connection, provider: Provider, email: str, context: Context
) -> Account:
    """Add the account, or re-enable it and update its context if it is already known."""
    (row,) = conn.execute(
        "INSERT INTO lm_accounts (provider, email, context, created_at) VALUES (?, ?, ?, ?) "
        "ON CONFLICT (provider, email) DO UPDATE SET context = excluded.context, enabled = 1 "
        "RETURNING *",
        (provider, email.lower(), context, utc_now()),
    ).fetchall()
    conn.commit()
    account = _to_account(row)
    logger.debug("Upserted account %s (%s)", account.key, account.context)
    return account


def list_accounts(conn: sqlite3.Connection, provider: Provider | None = None) -> list[Account]:
    """Enabled accounts, optionally only those of one provider."""
    rows = conn.execute(
        "SELECT * FROM lm_accounts WHERE enabled = 1 AND (:p IS NULL OR provider = :p) ORDER BY id",
        {"p": provider},
    ).fetchall()
    return [_to_account(row) for row in rows]


def _to_account(row: sqlite3.Row) -> Account:
    return Account(
        id=row["id"],
        provider=cast(Provider, row["provider"]),
        email=row["email"],
        context=cast(Context, row["context"]),
        enabled=bool(row["enabled"]),
    )

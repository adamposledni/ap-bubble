"""Command line of the ingest component: connect and list accounts, sync sources into L0."""

import argparse
import sqlite3
from collections.abc import Callable
from contextlib import closing

from bubble_core.accounts import CONTEXTS, list_accounts
from bubble_core.db import open_vault
from bubble_core.log import get_logger, setup_logging
from bubble_ingest.connect import connect_google
from bubble_ingest.google.calendar import sync as google_calendar
from bubble_ingest.google.contacts import sync as google_contacts
from bubble_ingest.google.tasks import sync as google_tasks

APP_NAME = "ap-bubble-ingest"
CONNECTORS: dict[str, Callable] = {"google": connect_google}
SYNCS: dict[str, Callable[[sqlite3.Connection], None]] = {
    "google_calendar": google_calendar.sync_all,
    "google_tasks": google_tasks.sync_all,
    "google_contacts": google_contacts.sync_all,
}

logger = get_logger(__name__)


def main(argv: list[str] | None = None) -> None:
    setup_logging(APP_NAME)
    args = _parser().parse_args(argv)
    try:
        args.handler(args)
    except Exception:
        logger.exception("Command failed")
        raise SystemExit(1) from None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=APP_NAME)
    commands = parser.add_subparsers(required=True)

    connect = commands.add_parser("connect", help="log in to an account and connect it")
    connect.add_argument("provider", choices=CONNECTORS)
    connect.add_argument("--context", choices=CONTEXTS, required=True)
    connect.set_defaults(handler=lambda args: CONNECTORS[args.provider](args.context))

    accounts = commands.add_parser("accounts", help="list connected accounts")
    accounts.set_defaults(handler=lambda _: _print_accounts())

    sync = commands.add_parser("sync", help="ingest a source's changes into L0, all accounts")
    sync.add_argument("source", choices=SYNCS)
    sync.set_defaults(handler=lambda args: _run_sync(args.source))
    return parser


def _print_accounts() -> None:
    with closing(open_vault()) as conn:
        for account in list_accounts(conn):
            print(f"{account.id:>3}  {account.key:<45} {account.context}")


def _run_sync(source: str) -> None:
    with closing(open_vault()) as conn:
        SYNCS[source](conn)

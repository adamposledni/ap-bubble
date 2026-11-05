"""Command line of the ingest component: connect and list accounts (sync commands follow)."""

import argparse
from collections.abc import Callable
from contextlib import closing

from bubble_core.accounts import CONTEXTS, list_accounts
from bubble_core.db import open_vault
from bubble_core.log import get_logger, setup_logging
from bubble_ingest.connect import connect_google

APP_NAME = "ap-bubble-ingest"
CONNECTORS: dict[str, Callable] = {"google": connect_google}

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
    return parser


def _print_accounts() -> None:
    with closing(open_vault()) as conn:
        for account in list_accounts(conn):
            print(f"{account.id:>3}  {account.key:<45} {account.context}")

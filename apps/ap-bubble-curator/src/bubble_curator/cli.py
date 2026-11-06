"""Command line of the curator: `run`, optionally as a dry run that only writes batch files."""

import argparse
from contextlib import closing

from bubble_core.db import open_vault
from bubble_core.log import get_logger, setup_logging
from bubble_curator.run import Options, run
from bubble_curator.settings import MAX_ITEMS_PER_RUN, WINDOW_DAYS

APP_NAME = "ap-bubble-curator"

logger = get_logger(__name__)


def main(argv: list[str] | None = None) -> None:
    setup_logging(APP_NAME)
    args = _parser().parse_args(argv)
    options = Options(dry_run=args.dry_run, max_items=args.max_items, window_days=args.window_days)
    try:
        with closing(open_vault()) as conn:
            run(conn, options)
    except Exception:
        logger.exception("Curator run failed")
        raise SystemExit(1) from None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=APP_NAME)
    commands = parser.add_subparsers(required=True)
    run_command = commands.add_parser("run", help="curate queued inputs and recent L0 changes")
    run_command.add_argument(
        "--dry-run", action="store_true", help="only write the batch files; no Claude, no changes"
    )
    run_command.add_argument("--max-items", type=int, default=MAX_ITEMS_PER_RUN)
    run_command.add_argument("--window-days", type=int, default=WINDOW_DAYS)
    return parser

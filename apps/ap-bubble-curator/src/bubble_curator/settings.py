"""Limits and defaults of a curator run; the CLI can override the first three."""

WINDOW_DAYS = 30  # only L0 items of the last N days (open tasks and contacts always)
MAX_ITEMS_PER_RUN = 300  # L0 items kept per run; the rest waits for the next run
MAX_INPUTS_PER_RUN = 20  # queued L1 inputs per run
MAX_BATCH_CHARS = 60_000  # text per batch file, i.e. per Claude call
MAX_TEXT_CHARS = 1_500  # per message, note or description
CLAUDE_TIMEOUT_SECONDS = 30 * 60
CLAUDE_COMMAND_ENV = "BUBBLE_CLAUDE_COMMAND"  # default: 'claude' on PATH
# An ingest run still 'running' after this long is taken as dead and no longer holds back curation.
RUNNING_RUN_TIMEOUT_HOURS = 6

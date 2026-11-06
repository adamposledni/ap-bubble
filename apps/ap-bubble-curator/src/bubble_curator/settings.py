"""Limits and defaults of a curator run; the CLI can override the first three."""

WINDOW_DAYS = 30  # only L0 items of the last N days (open tasks and contacts always)
MAX_ITEMS_PER_RUN = 300  # L0 items kept per run; the rest waits for the next run
MAX_INPUTS_PER_RUN = 20  # queued L1 inputs per run
MAX_INPUT_ATTEMPTS = 3  # a failed input is retried by the next runs until it failed this often
MAX_BATCH_CHARS = 60_000  # text per batch file, i.e. per Claude call
FILE_CHARS = 15_000  # batch weight of one attached file Claude has to read
MAX_TEXT_CHARS = 1_500  # per message, note or description
# Events of calendars whose external id contains one of these are noise.
SKIPPED_CALENDAR_PATTERNS = (
    "#holiday@group.v.calendar.google.com",  # any Google public holiday calendar
    "quh6h0ajl2qtrouii90g38el9davgdt3@import.calendar.google.com",  # Julie's work shifts
)
MIN_PHONE_DIGITS = 5  # a contact needs a phone number with more digits than this (or an email)
CLAUDE_TIMEOUT_SECONDS = 30 * 60
CLAUDE_COMMAND_ENV = "BUBBLE_CLAUDE_COMMAND"  # default: 'claude' on PATH
CLAUDE_MODEL = "claude-opus-5-5"
CLAUDE_MODEL_ENV = "BUBBLE_CURATOR_MODEL"
CLAUDE_EFFORT = "medium"  # low / medium / high / xhigh / max
CLAUDE_EFFORT_ENV = "BUBBLE_CURATOR_EFFORT"
# An ingest run still 'running' after this long is taken as dead and no longer holds back curation.
RUNNING_RUN_TIMEOUT_HOURS = 6

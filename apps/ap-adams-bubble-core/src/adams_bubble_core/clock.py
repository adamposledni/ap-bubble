"""Timestamps as stored in the vault: ISO 8601, UTC, second precision."""

from datetime import UTC, datetime


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")

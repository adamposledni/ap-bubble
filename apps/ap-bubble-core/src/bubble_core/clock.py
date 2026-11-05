"""Timestamps as stored in the vault: ISO 8601, UTC, second precision."""

from datetime import UTC, datetime


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def to_utc(timestamp: str) -> str:
    """Convert an ISO 8601 timestamp with an offset (e.g. +01:00 or Z) to the stored form."""
    return datetime.fromisoformat(timestamp).astimezone(UTC).isoformat(timespec="seconds")

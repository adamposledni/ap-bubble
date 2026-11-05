"""Start and end of Google Calendar events as aware datetimes; all-day ones at local midnight."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Span:
    start: datetime
    end: datetime
    all_day: bool

    def overlaps(self, start: datetime, end: datetime) -> bool:
        return self.start < end and self.end > start

    def moved_to(self, start: datetime) -> "Span":
        return Span(start, start + (self.end - self.start), self.all_day)


def span_of(event: dict[str, Any], tz: ZoneInfo) -> Span:
    """The event's span; all-day dates become midnight in tz (the end date is exclusive)."""
    start, end = event["start"], event["end"]
    return Span(moment_of(start, tz), moment_of(end, tz), all_day="date" in start)


def moment_of(when: dict[str, str], tz: ZoneInfo) -> datetime:
    """A start/end/originalStartTime value; timed ones in their own time zone when given."""
    if "date" in when:
        return datetime.combine(date.fromisoformat(when["date"]), time(), tz)
    moment = datetime.fromisoformat(when["dateTime"])
    return moment.astimezone(ZoneInfo(when["timeZone"])) if "timeZone" in when else moment


def as_text(moment: datetime, all_day: bool) -> str:
    """A date for all-day events, else the vault's UTC timestamp form."""
    if all_day:
        return moment.date().isoformat()
    return moment.astimezone(UTC).isoformat(timespec="seconds")


def day_window(first_day: date, days: int, tz: ZoneInfo) -> tuple[datetime, datetime]:
    start = datetime.combine(first_day, time(), tz)
    return start, datetime.combine(first_day + timedelta(days=days), time(), tz)

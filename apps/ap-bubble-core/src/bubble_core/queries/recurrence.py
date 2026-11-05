"""Occurrences of recurring events defined by iCalendar RRULE / EXDATE / RDATE lines."""

import re
from datetime import UTC, date, datetime, time, tzinfo
from zoneinfo import ZoneInfo

from dateutil.rrule import rruleset, rrulestr

_DATE_ONLY_UNTIL = re.compile(r"UNTIL=(\d{8})(?=;|$)")


def occurrence_starts(
    dtstart: datetime, recurrence: list[str], after: datetime, before: datetime
) -> list[datetime]:
    """Starts of the occurrences between after and before (inclusive); dtstart must be aware."""
    rules = rruleset()
    for line in recurrence:
        head, _, value = line.partition(":")
        name, *params = head.split(";")
        if name == "RRULE":
            rules.rrule(rrulestr(_utc_until(value), dtstart=dtstart))
        elif name == "EXDATE":
            for moment in _moments(value, params, dtstart.tzinfo):
                rules.exdate(moment)
        elif name == "RDATE":
            for moment in _moments(value, params, dtstart.tzinfo):
                rules.rdate(moment)
    return rules.between(after, before, inc=True)


def _utc_until(rule: str) -> str:
    """A date-only UNTIL as the end of that day in UTC: an aware DTSTART needs a UTC UNTIL."""
    return _DATE_ONLY_UNTIL.sub(r"UNTIL=\1T235959Z", rule)


def _moments(value: str, params: list[str], default_tz: tzinfo | None) -> list[datetime]:
    tzid = next((p.removeprefix("TZID=") for p in params if p.startswith("TZID=")), None)
    tz = ZoneInfo(tzid) if tzid else default_tz
    return [_moment(text, tz) for text in value.split(",")]


def _moment(text: str, tz: tzinfo | None) -> datetime:
    if len(text) == 8:  # VALUE=DATE: midnight of that day
        day = date(int(text[:4]), int(text[4:6]), int(text[6:]))
        return datetime.combine(day, time(), tz)
    if text.endswith("Z"):
        return datetime.strptime(text, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    return datetime.strptime(text, "%Y%m%dT%H%M%S").replace(tzinfo=tz)

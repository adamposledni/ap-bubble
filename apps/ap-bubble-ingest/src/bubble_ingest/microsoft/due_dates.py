"""Due dates of Microsoft tasks as the local day (YYYY-MM-DD) their due moment falls on.

Planner and To Do send a due date as a moment in UTC. To Do sends midnight of the due day in my
zone, i.e. 22:00 or 23:00 UTC the day before; Planner sends 10:00 UTC. Read in the local zone,
both give the due day back.
"""

from datetime import UTC, datetime, tzinfo
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from bubble_core.log import get_logger

LOCAL_ZONE: tzinfo | None = None  # None: this PC's time zone

logger = get_logger(__name__)


def day_of_timestamp(timestamp: str | None) -> str | None:
    """The local day of an ISO 8601 timestamp with an offset, e.g. Planner's dueDateTime."""
    if not timestamp:
        return None
    return _local_day(datetime.fromisoformat(timestamp))


def day_of_date_time_zone(value: dict[str, Any] | None) -> str | None:
    """The local day of a Graph dateTimeTimeZone, e.g. To Do's dueDateTime.

    Graph sends UTC unless asked for another zone; a zone that zoneinfo does not know (a Windows
    name) keeps the date as sent.
    """
    if not value or not value.get("dateTime"):
        return None
    moment = datetime.fromisoformat(value["dateTime"])
    try:
        zone = ZoneInfo(value.get("timeZone") or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        logger.debug("Unknown time zone %r; keeping the date as sent", value.get("timeZone"))
        return moment.date().isoformat()
    return _local_day(moment.replace(tzinfo=zone))


def _local_day(moment: datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(LOCAL_ZONE).date().isoformat()

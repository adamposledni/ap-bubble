"""Events, tasks and contacts as units: one per item."""

from typing import Any

from bubble_core.text import body_text
from bubble_curator.changes import ChangedItem
from bubble_curator.unit import Unit, clip, local_time, ref


def record_unit(item: ChangedItem) -> Unit:
    render = {"event": _event, "task": _task, "contact": _contact}[item.kind]
    heading, lines = render(item)
    body = "\n".join(f"- {line}" for line in lines if line)
    sort_key = f"1{item.starts_at or ''}"
    return Unit(f"{heading} [{ref(item.id)}] ({item.context})", body, sort_key, [item.id])


def _event(item: ChangedItem) -> tuple[str, list[str | None]]:
    p = item.payload
    when = f"{local_time(item.starts_at)} – {local_time(item.ends_at)}"
    location = p.get("location")
    location = location.get("displayName") if isinstance(location, dict) else location
    description = p.get("description") or p.get("bodyPreview") or body_text(p.get("body"))
    return f"Event: {item.title or '(no title)'}", [
        f"When: {when}",
        f"Where: {location}" if location else None,
        f"Organizer: {_person(p.get('organizer'))}" if p.get("organizer") else None,
        _attendees(p.get("attendees", [])),
        f"Repeats: {', '.join(p['recurrence'])}" if p.get("recurrence") else None,
        f"Description: {clip(description)}" if description else None,
    ]


def _task(item: ChangedItem) -> tuple[str, list[str | None]]:
    p = item.payload
    notes = p.get("notes") or body_text(p.get("body"))
    done = p.get("status") == "completed" or (p.get("percentComplete") or 0) >= 100
    return f"Task: {item.title or '(no title)'}", [
        f"Due: {item.starts_at}" if item.starts_at else None,
        f"Status: {'done' if done else 'open'} ({item.source})",
        f"Notes: {clip(notes)}" if notes else None,
    ]


def _contact(item: ChangedItem) -> tuple[str, list[str | None]]:
    p = item.payload
    return f"Contact: {item.title or '(no name)'}", [
        _values("Emails", p.get("emailAddresses"), "value"),
        _values("Phones", p.get("phoneNumbers"), "value"),
        _values("Nicknames", p.get("nicknames"), "value"),
        _birthday(p.get("birthdays")),
        _values("Organization", p.get("organizations"), "name", "title"),
        _values("Addresses", p.get("addresses"), "formattedValue"),
        _values("Relations", p.get("relations"), "person", "type"),
        _values("Notes", p.get("biographies"), "value"),
    ]


def _values(label: str, entries: list[dict[str, Any]] | None, *keys: str) -> str | None:
    values = [" / ".join(str(e[k]) for k in keys if e.get(k)) for e in entries or []]
    values = [clip(v) for v in values if v]
    return f"{label}: {'; '.join(values)}" if values else None


def _birthday(birthdays: list[dict[str, Any]] | None) -> str | None:
    date = next((b.get("date") for b in birthdays or [] if b.get("date")), None)
    if not date:
        return None
    parts = [str(date[k]) for k in ("year", "month", "day") if date.get(k)]
    return f"Birthday: {'-'.join(parts)}"


def _attendees(attendees: list[dict[str, Any]]) -> str | None:
    names = [_person(a) for a in attendees]
    return f"Attendees: {', '.join(n for n in names if n)}" if names else None


def _person(entry: dict[str, Any] | None) -> str:
    entry = entry or {}
    email = entry.get("emailAddress") or {}
    return (
        entry.get("displayName")
        or email.get("name")
        or entry.get("email")
        or email.get("address")
        or ""
    )

"""The YAML front matter of a knowledge file, read without a YAML parser (top-level keys only)."""

_FENCE = "---"


def split_front_matter(text: str) -> tuple[dict[str, str], str]:
    """(top-level 'key: value' lines of the front matter, the markdown body after it).

    [a, b] lists become 'a, b'; see list_value. Without front matter the whole text is the body.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FENCE:
        return {}, text
    meta: dict[str, str] = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == _FENCE:
            return meta, "\n".join(lines[index + 1 :]).strip()
        key, separator, value = line.partition(":")
        if separator and not line.startswith((" ", "-")):
            meta[key.strip()] = value.strip().strip("[]").strip()
    return meta, ""


def front_matter(text: str) -> dict[str, str]:
    return split_front_matter(text)[0]


def list_value(value: str | None) -> list[str]:
    """'a, "b"' -> ['a', 'b']."""
    items = (unquote(item) for item in (value or "").split(","))
    return [item for item in items if item]


def unquote(value: str) -> str:
    return value.strip().strip("\"'").strip()

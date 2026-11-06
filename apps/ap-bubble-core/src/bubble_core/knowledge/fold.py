"""Case- and diacritics-insensitive matching: 'Novák' and 'NOVAK' both fold to 'novak'."""

import unicodedata
from functools import cache


def fold(text: str) -> str:
    return "".join(_fold_char(char) for char in text)


def fold_with_map(text: str) -> tuple[str, list[int]]:
    """The folded text and, per folded character, the index of its character in text."""
    parts: list[str] = []
    origin: list[int] = []
    for index, char in enumerate(text):
        folded = _fold_char(char)
        parts.append(folded)
        origin.extend([index] * len(folded))
    return "".join(parts), origin


def find_all(text: str, terms: list[str]) -> list[tuple[int, int]]:
    """Sorted, merged [start, end) spans of text where any folded term occurs."""
    folded, origin = fold_with_map(text)
    spans = sorted(
        (origin[start], origin[start + len(term) - 1] + 1)
        for term in terms
        for start in _starts(folded, term)
    )
    return _merged(spans)


def _starts(text: str, term: str) -> list[int]:
    starts, start = [], text.find(term)
    while term and start >= 0:
        starts.append(start)
        start = text.find(term, start + len(term))
    return starts


def _merged(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


@cache
def _fold_char(char: str) -> str:
    decomposed = unicodedata.normalize("NFD", char)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()

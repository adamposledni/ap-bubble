from typing import Any

import pytest

from bubble_ingest.microsoft.calendar import api
from bubble_ingest.microsoft.graph import GRAPH_URL, Pages

WINDOW = api.Window("2026-01-01T00:00:00Z", "2028-01-01T00:00:00Z")
PREFER = 'outlook.timezone="UTC", IdType="ImmutableId"'


class Recorder:
    """Stands in for a graph function: records its arguments and returns the given pages."""

    def __init__(self, pages: Pages) -> None:
        self.pages = pages
        self.calls: list[tuple[Any, ...]] = []

    def __call__(self, session: object, *args: Any) -> Pages:
        self.calls.append(args)
        return self.pages


def test_default_calendar_changes_continue_from_the_delta_link(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_delta = Recorder(Pages([{"id": "e1"}], "https://delta-2"))
    monkeypatch.setattr(api, "get_delta", get_delta)

    changes = api.default_calendar_changes(object(), WINDOW, "https://delta-1")  # type: ignore[arg-type]

    assert (changes.events, changes.delta_link) == ([{"id": "e1"}], "https://delta-2")
    [(url, params, delta_link, headers)] = get_delta.calls
    assert url == f"{GRAPH_URL}/me/calendarView/delta"
    assert params == {"startDateTime": WINDOW.start, "endDateTime": WINDOW.end}
    assert (delta_link, headers) == ("https://delta-1", {"Prefer": PREFER})


def test_delta_without_a_delta_link_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api, "get_delta", Recorder(Pages([], None)))

    with pytest.raises(RuntimeError):
        api.default_calendar_changes(object(), WINDOW, None)  # type: ignore[arg-type]


def test_calendar_view_reads_the_window_of_one_calendar(monkeypatch: pytest.MonkeyPatch) -> None:
    get_all_pages = Recorder(Pages([{"id": "e1"}], None))
    monkeypatch.setattr(api, "get_all_pages", get_all_pages)

    events = api.calendar_view(object(), "AAMk/cal=", WINDOW)  # type: ignore[arg-type]

    assert events == [{"id": "e1"}]
    [(url, params, headers)] = get_all_pages.calls
    assert url == f"{GRAPH_URL}/me/calendars/AAMk%2Fcal%3D/calendarView"
    assert params == {"startDateTime": WINDOW.start, "endDateTime": WINDOW.end, "$top": 1000}
    assert headers == {"Prefer": PREFER}

from bubble_core.clock import to_utc


def test_to_utc_converts_an_offset() -> None:
    assert to_utc("2026-03-05T10:00:00+01:00") == "2026-03-05T09:00:00+00:00"


def test_to_utc_accepts_z() -> None:
    assert to_utc("2026-03-05T09:00:00Z") == "2026-03-05T09:00:00+00:00"

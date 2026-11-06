from bubble_ingest.microsoft.auth import SCOPES, missing_scopes


def test_no_scope_is_missing_when_all_are_granted_with_or_without_prefix() -> None:
    granted = "https://graph.microsoft.com/Mail.Read " + " ".join(SCOPES[1:]) + " openid profile"
    granted += " " + SCOPES[0].lower()

    assert missing_scopes(granted) == []


def test_scopes_not_granted_are_reported() -> None:
    granted = " ".join(scope for scope in SCOPES if scope != "Chat.Read")

    assert missing_scopes(granted) == ["Chat.Read"]

from bubble_ingest.google.contacts.mapping import to_item


def test_contact_is_titled_by_its_display_name() -> None:
    person = {
        "resourceName": "people/c1",
        "names": [{"displayName": "Petr Novák"}],
        "emailAddresses": [{"value": "petr@example.com"}],
        "birthdays": [{"date": {"month": 3, "day": 5}}],
    }

    item = to_item("connections", person)

    assert (item.container_id, item.external_id, item.kind, item.title) == (
        "connections",
        "people/c1",
        "contact",
        "Petr Novák",
    )
    assert (item.starts_at, item.ends_at) == (None, None)
    assert not item.deleted
    assert item.payload == person


def test_primary_name_wins_over_the_first() -> None:
    names = [{"displayName": "Profile"}, {"displayName": "Own", "metadata": {"primary": True}}]

    item = to_item("connections", {"resourceName": "people/c1", "names": names})

    assert item.title == "Own"


def test_contact_without_name_is_titled_by_its_email() -> None:
    person = {"resourceName": "otherContacts/c1", "emailAddresses": [{"value": "a@example.com"}]}

    assert to_item("other", person).title == "a@example.com"


def test_deletion_stub_is_deleted_and_untitled() -> None:
    item = to_item("connections", {"resourceName": "people/c1", "metadata": {"deleted": True}})

    assert item.deleted
    assert item.title is None

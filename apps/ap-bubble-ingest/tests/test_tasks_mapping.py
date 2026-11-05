from bubble_ingest.google.tasks.mapping import to_item


def test_task_with_due_date_starts_on_that_date() -> None:
    task = {
        "id": "t1",
        "title": "Pay rent",
        "status": "needsAction",
        "due": "2026-03-05T00:00:00.000Z",
        "notes": "by transfer",
    }

    item = to_item("list1", task)

    assert (item.source, item.kind) == ("google_tasks", "task")
    assert (item.container_id, item.external_id, item.title) == ("list1", "t1", "Pay rent")
    assert (item.starts_at, item.ends_at) == ("2026-03-05", None)
    assert not item.deleted
    assert item.payload == task


def test_task_without_due_date_has_no_start() -> None:
    item = to_item("list1", {"id": "t1", "title": "Someday"})

    assert item.starts_at is None


def test_deleted_task_is_deleted() -> None:
    item = to_item("list1", {"id": "t1", "deleted": True})

    assert item.deleted

from bubble_core.paths import knowledge_dir
from bubble_curator.cleanup import remove_deleted_files

KEPT = "---\nname: Petr Novák\ndeleted: false\n---\n\n## Summary\n"
MARKED = "---\ndeleted: true\n---\n"


def test_removes_only_files_marked_deleted() -> None:
    people = knowledge_dir() / "people"
    people.mkdir(parents=True)
    (people / "petr-novak.md").write_text(KEPT, encoding="utf-8")
    (people / "petr.md").write_text(MARKED, encoding="utf-8")
    (people / "no-front-matter.md").write_text("# Jana", encoding="utf-8")

    removed = remove_deleted_files()

    assert removed == ["people/petr"]
    assert sorted(path.name for path in people.iterdir()) == ["no-front-matter.md", "petr-novak.md"]


def test_empty_knowledge_base_removes_nothing() -> None:
    assert remove_deleted_files() == []

import pytest

from bubble_core.knowledge import KnowledgeNotFound, front_matter, list_files, read_file
from bubble_core.knowledge.front_matter import split_front_matter
from bubble_core.paths import knowledge_dir

PETR = """---
name: "Petr Novák"
aliases: [Petr, Péťa]
emails: [petr@example.com]
phones: []
tags: [work, databrothers]
updated: 2026-11-06
---

## Summary
Colleague.
"""


def write(ref: str, text: str) -> None:
    path = knowledge_dir() / f"{ref}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_front_matter_reads_top_level_keys_only() -> None:
    meta = front_matter("---\nname: A\nnested:\n  key: x\n---\nname: not this")

    assert meta == {"name": "A", "nested": ""}


def test_text_without_front_matter_is_all_body() -> None:
    assert split_front_matter("# Jana\nText") == ({}, "# Jana\nText")


def test_read_file_parses_meta_and_body() -> None:
    write("people/petr-novak", PETR)

    file = read_file("people", "petr-novak")

    assert (file.ref, file.body) == ("people/petr-novak", "## Summary\nColleague.")
    assert file.meta.name == "Petr Novák"
    assert (file.meta.aliases, file.meta.phones) == (["Petr", "Péťa"], [])
    assert (file.meta.tags, file.meta.updated) == (["work", "databrothers"], "2026-11-06")


def test_name_falls_back_to_the_slug() -> None:
    write("topics/cars", "Just text")

    assert read_file("topics", "cars").meta.name == "cars"


def test_list_files_skips_questions_and_other_folders() -> None:
    write("people/petr-novak", PETR)
    write("places/povrly", "x")
    write("questions", "- Is Petr the same?")
    write("archive/old", "x")

    assert [f.ref for f in list_files()] == ["people/petr-novak", "places/povrly"]
    assert [f.ref for f in list_files("places")] == ["places/povrly"]


@pytest.mark.parametrize(
    ("folder", "slug"),
    [("people", "missing"), ("other", "x"), ("people", "..\\..\\vault"), ("people", ".hidden")],
)
def test_only_existing_files_in_known_folders_are_read(folder: str, slug: str) -> None:
    write("other/x", "x")

    with pytest.raises(KnowledgeNotFound):
        read_file(folder, slug)  # type: ignore[arg-type]

import pytest

from bubble_core.knowledge import KnowledgeRef, knowledge_doc
from bubble_core.knowledge.links import resolve_link
from bubble_core.paths import knowledge_dir


def write(ref: str, name: str, body: str) -> None:
    path = knowledge_dir() / f"{ref}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nname: {name}\n---\n{body}", encoding="utf-8")


@pytest.mark.parametrize(
    ("href", "ref"),
    [
        ("../people/petr-novak.md", "people/petr-novak"),
        ("jana-hroudova.md", "people/jana-hroudova"),
        ("../places/povrly.md", "places/povrly"),
        ("../questions.md", None),
        ("../../vault.md", None),
        ("https://example.com/a.md", None),
        ("../people/notes.txt", None),
    ],
)
def test_resolve_link_from_a_people_file(href: str, ref: str | None) -> None:
    assert resolve_link("people", href) == ref


def test_doc_lists_the_files_linking_to_it() -> None:
    write("people/petr-novak", "Petr Novák", "Linked from [self](petr-novak.md).")
    write("people/jana", "Jana", "Knows [Petr](petr-novak.md).")
    write("topics/work", "Work", "Team: [Petr Novák](../people/petr-novak.md#facts).")
    write("topics/other", "Other", "Mentions Petr without a link.")

    doc = knowledge_doc("people", "petr-novak")

    assert doc.meta.name == "Petr Novák"
    assert doc.backlinks == [
        KnowledgeRef("people", "jana", "Jana"),
        KnowledgeRef("topics", "work", "Work"),
    ]

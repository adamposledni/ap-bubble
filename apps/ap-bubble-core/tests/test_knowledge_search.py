import sqlite3
from pathlib import Path

import pytest

from bubble_core.knowledge import Folder, KnowledgeFile, search, sync_index
from bubble_core.knowledge import index as knowledge_index
from bubble_core.knowledge.fold import find_all, fold
from bubble_core.knowledge.plain import plain_text
from bubble_core.knowledge.snippet import SnippetPart, snippet
from bubble_core.paths import knowledge_dir


def write(ref: str, name: str, body: str = "", tags: str = "", updated: str = "2026-11-01") -> None:
    path = knowledge_dir() / f"{ref}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = f"---\nname: {name}\ntags: [{tags}]\nupdated: {updated}\n---\n"
    path.write_text(meta + body, encoding="utf-8")


def refs(conn: sqlite3.Connection, query: str, folder: str | None = None) -> list[str]:
    hits = search(conn, query, folder).hits  # type: ignore[arg-type]
    return [f"{h.folder}/{h.slug}" for h in hits]


def indexed(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT ref FROM l2_knowledge_files ORDER BY ref")
    return [row["ref"] for row in rows]


def test_fold_drops_case_and_diacritics() -> None:
    assert fold("Štěpán NOVÁK") == "stepan novak"


def test_find_all_maps_folded_matches_back_to_the_text() -> None:
    assert find_all("Petr Novák, novák", ["novak", "petr"]) == [(0, 4), (5, 10), (12, 17)]


def test_search_ignores_case_and_diacritics(conn: sqlite3.Connection) -> None:
    write("people/petr-novak", "Petr Novák")
    write("people/jana", "Jana")

    assert refs(conn, "NOVAK") == ["people/petr-novak"]
    assert refs(conn, "nováka") == []


def test_words_match_as_prefixes_not_inside_words(conn: sqlite3.Connection) -> None:
    write("people/petr-novak", "Petr Novák", "Works at Linet.")

    assert refs(conn, "nov lin") == ["people/petr-novak"]
    assert refs(conn, "ovak") == []


def test_all_words_must_match(conn: sqlite3.Connection) -> None:
    write("people/petr-novak", "Petr Novák", "Works at Linet.")
    write("people/petr-hrouda", "Petr Hrouda")

    assert refs(conn, "petr linet") == ["people/petr-novak"]


def test_name_matches_rank_above_tags_above_body(conn: sqlite3.Connection) -> None:
    write("people/in-body", "Body", "Met at the DataBrothers office.", updated="2026-11-06")
    write("people/in-tags", "Tags", tags="databrothers", updated="2026-11-05")
    write("topics/databrothers", "DataBrothers", updated="2026-10-01")

    expected = ["topics/databrothers", "people/in-tags", "people/in-body"]
    assert refs(conn, "databrothers") == expected


def test_email_matches_as_one_word(conn: sqlite3.Connection) -> None:
    write("people/petr-novak", "Petr Novák", "Mail: petr.novak@linet.cz")
    write("people/jana", "Jana", "Mail: jana@linet.cz")

    assert refs(conn, "petr.novak@linet.cz") == ["people/petr-novak"]


def test_empty_query_lists_all_newest_first_within_the_folder(conn: sqlite3.Connection) -> None:
    write("people/old", "Old", updated="2026-01-01")
    write("people/new", "New", updated="2026-11-06")
    write("places/povrly", "Povrly", updated="2026-11-07")

    assert refs(conn, "  ", "people") == ["people/new", "people/old"]


def test_total_counts_matches_beyond_the_limit(conn: sqlite3.Connection) -> None:
    for index in range(3):
        write(f"people/p{index}", f"Person {index}")

    result = search(conn, "person", limit=2)

    assert (result.total, len(result.hits)) == (3, 2)


@pytest.mark.parametrize("query", ['"petr', "petr*", "(petr)", "-petr", "petr^", "petr -"])
def test_query_syntax_characters_are_plain_text(conn: sqlite3.Connection, query: str) -> None:
    write("people/petr-novak", "Petr Novák")
    write("people/jana", "Jana")

    assert refs(conn, query) == ["people/petr-novak"]


def test_query_operators_are_plain_words(conn: sqlite3.Connection) -> None:
    write("people/petr-novak", "Petr Novák")
    write("people/jana", "Jana")

    assert refs(conn, "petr OR jana") == []
    assert refs(conn, "NOT jana") == []


def test_query_of_punctuation_only_lists_all(conn: sqlite3.Connection) -> None:
    write("people/petr-novak", "Petr Novák")

    assert refs(conn, '" * ( :') == ["people/petr-novak"]


def test_sync_indexes_new_changed_and_removes_deleted_files(conn: sqlite3.Connection) -> None:
    write("people/jana", "Jana", "Lives in Povrly.")
    write("people/petr", "Petr")
    sync_index(conn)

    write("people/jana", "Jana", "Moved to Ústí nad Labem.")  # another size: a change
    (knowledge_dir() / "people" / "petr.md").unlink()
    write("places/povrly", "Povrly")

    assert refs(conn, "usti") == ["people/jana"]
    assert refs(conn, "povrly") == ["places/povrly"]
    assert indexed(conn) == ["people/jana", "places/povrly"]


def test_sync_reads_only_new_or_changed_files(
    conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    write("people/jana", "Jana")
    sync_index(conn)
    loaded: list[str] = []
    load_file = knowledge_index.load_file

    def counting_load_file(folder: Folder, path: Path) -> KnowledgeFile:
        loaded.append(path.stem)
        return load_file(folder, path)

    monkeypatch.setattr(knowledge_index, "load_file", counting_load_file)

    sync_index(conn)
    write("people/petr", "Petr")
    sync_index(conn)

    assert loaded == ["petr"]


def test_hit_snippet_highlights_the_body_match(conn: sqlite3.Connection) -> None:
    write("people/jana", "Jana", "## Summary\nLives in [Povrly](../places/povrly.md).")

    [hit] = search(conn, "povrly").hits

    assert hit.snippet == [
        SnippetPart("Lives in ", match=False),
        SnippetPart("Povrly", match=True),
        SnippetPart(".", match=False),
    ]


def test_plain_text_drops_headings_links_and_markup() -> None:
    markdown = "## Facts\n- **Wife**: [Julie](julie.md) (input:4)\n- Second"

    assert plain_text(markdown) == "Wife: Julie (input:4) · Second"


def test_long_snippet_is_cut_around_the_match() -> None:
    text = " ".join(["word"] * 100) + " target " + " ".join(["word"] * 100)

    parts = snippet(text, ["target"])

    excerpt = "".join(part.text for part in parts)
    assert excerpt.startswith("…word") and excerpt.endswith("word…")
    assert len(excerpt) <= 182
    assert [part.text for part in parts if part.match] == ["target"]

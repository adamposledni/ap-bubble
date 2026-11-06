from bubble_core.knowledge import search
from bubble_core.knowledge.fold import find_all, fold
from bubble_core.knowledge.plain import plain_text
from bubble_core.knowledge.snippet import SnippetPart, snippet
from bubble_core.paths import knowledge_dir


def write(ref: str, name: str, body: str = "", tags: str = "", updated: str = "2026-11-01") -> None:
    path = knowledge_dir() / f"{ref}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = f"---\nname: {name}\ntags: [{tags}]\nupdated: {updated}\n---\n"
    path.write_text(meta + body, encoding="utf-8")


def refs(query: str, folder: str | None = None) -> list[str]:
    return [f"{h.folder}/{h.slug}" for h in search(query, folder).hits]  # type: ignore[arg-type]


def test_fold_drops_case_and_diacritics() -> None:
    assert fold("Štěpán NOVÁK") == "stepan novak"


def test_find_all_maps_folded_matches_back_to_the_text() -> None:
    assert find_all("Petr Novák, novák", ["novak", "petr"]) == [(0, 4), (5, 10), (12, 17)]


def test_search_ignores_case_and_diacritics() -> None:
    write("people/petr-novak", "Petr Novák")
    write("people/jana", "Jana")

    assert refs("NOVAK") == ["people/petr-novak"]


def test_all_words_must_match() -> None:
    write("people/petr-novak", "Petr Novák", "Works at Linet.")
    write("people/petr-hrouda", "Petr Hrouda")

    assert refs("petr linet") == ["people/petr-novak"]


def test_name_matches_rank_above_tags_above_body() -> None:
    write("people/in-body", "Body", "Met at the DataBrothers office.", updated="2026-11-06")
    write("people/in-tags", "Tags", tags="databrothers", updated="2026-11-05")
    write("topics/databrothers", "DataBrothers", updated="2026-10-01")

    assert refs("databrothers") == ["topics/databrothers", "people/in-tags", "people/in-body"]


def test_empty_query_lists_all_newest_first_within_the_folder() -> None:
    write("people/old", "Old", updated="2026-01-01")
    write("people/new", "New", updated="2026-11-06")
    write("places/povrly", "Povrly", updated="2026-11-07")

    assert refs("  ", "people") == ["people/new", "people/old"]


def test_total_counts_matches_beyond_the_limit() -> None:
    for index in range(3):
        write(f"people/p{index}", f"Person {index}")

    result = search("person", limit=2)

    assert (result.total, len(result.hits)) == (3, 2)


def test_hit_snippet_highlights_the_body_match() -> None:
    write("people/jana", "Jana", "## Summary\nLives in [Povrly](../places/povrly.md).")

    [hit] = search("povrly").hits

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

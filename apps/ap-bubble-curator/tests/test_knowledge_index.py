from pathlib import Path

from bubble_core.paths import knowledge_dir
from bubble_curator.knowledge_index import write_index

PETR = """---
name: Petr Novák
aliases: [Petr, Péťa]
emails: [petr@example.com]
tags: [work]
---

## Summary
"""


def test_index_lists_files_with_name_aliases_and_emails(tmp_path: Path) -> None:
    people = knowledge_dir() / "people"
    people.mkdir(parents=True)
    (people / "petr-novak.md").write_text(PETR, encoding="utf-8")
    (people / "no-front-matter.md").write_text("# Jana", encoding="utf-8")

    count = write_index(tmp_path / "index.md")

    text = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert count == 2
    assert "- people/petr-novak.md — Petr Novák (Petr, Péťa; petr@example.com)" in text
    assert "- people/no-front-matter.md — no-front-matter" in text


def test_empty_knowledge_base_says_so(tmp_path: Path) -> None:
    assert write_index(tmp_path / "index.md") == 0
    assert "(none yet)" in (tmp_path / "index.md").read_text(encoding="utf-8")

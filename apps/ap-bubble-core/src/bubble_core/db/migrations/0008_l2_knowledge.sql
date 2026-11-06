-- L2: search index over the knowledge files (<folder>/<slug>.md); the files stay the truth.
-- Rebuilt lazily: a file is re-read only when its mtime or size differ from the indexed ones.
CREATE TABLE l2_knowledge_files (
    id         INTEGER PRIMARY KEY,  -- rowid of the file's l2_knowledge_fts row
    ref        TEXT    NOT NULL UNIQUE,  -- 'folder/slug', e.g. 'people/petr-novak'
    folder     TEXT    NOT NULL,  -- 'people', 'places', 'topics' or 'me'
    slug       TEXT    NOT NULL,  -- file name without .md
    name       TEXT    NOT NULL,
    name_key   TEXT    NOT NULL,  -- name folded (no case, no diacritics): sort key
    tags       TEXT    NOT NULL,  -- JSON array of strings
    updated    TEXT,              -- YYYY-MM-DD from the front matter
    plain      TEXT    NOT NULL,  -- plain text of the body, for snippets
    mtime_ns   INTEGER NOT NULL,  -- of the file when indexed
    size_bytes INTEGER NOT NULL
);

CREATE INDEX ix_l2_knowledge_files_folder ON l2_knowledge_files (folder);

-- Full-text index, one row per file with rowid = l2_knowledge_files.id; holds folded text.
-- names: name, aliases, slug; details: tags, emails, phones; body: plain text of the body.
CREATE VIRTUAL TABLE l2_knowledge_fts USING fts5 (
    names,
    details,
    body,
    tokenize = 'unicode61 remove_diacritics 2'
);

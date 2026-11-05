-- L1: my own input (text and/or files), queued for the curator.
-- AUTOINCREMENT: ids are never reused, so an id always names the same inbox folder.
CREATE TABLE l1_inputs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    text         TEXT,     -- note or content; NULL when the input is files only
    status       TEXT    NOT NULL DEFAULT 'queued'
                         CHECK (status IN ('queued', 'processing', 'done', 'failed')),
    error        TEXT,
    created_at   TEXT    NOT NULL,  -- ISO 8601, UTC
    processed_at TEXT
);

CREATE INDEX ix_l1_inputs_status ON l1_inputs (status);

-- Files of an input, stored in the inbox folder.
CREATE TABLE l1_input_files (
    id          INTEGER PRIMARY KEY,
    input_id    INTEGER NOT NULL REFERENCES l1_inputs (id) ON DELETE CASCADE,
    file_name   TEXT    NOT NULL,  -- as uploaded
    stored_path TEXT    NOT NULL,  -- relative to the inbox folder
    media_type  TEXT,
    size_bytes  INTEGER NOT NULL
);

CREATE INDEX ix_l1_input_files_input_id ON l1_input_files (input_id);

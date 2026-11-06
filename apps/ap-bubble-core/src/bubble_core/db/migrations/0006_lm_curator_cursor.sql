-- Where the curator left off in the L0 change set, read in (changed_run_id, id) order. One row.
CREATE TABLE lm_curator_cursor (
    id             INTEGER PRIMARY KEY CHECK (id = 1),
    changed_run_id INTEGER NOT NULL,
    item_id        INTEGER NOT NULL,
    updated_at     TEXT    NOT NULL  -- ISO 8601, UTC
);

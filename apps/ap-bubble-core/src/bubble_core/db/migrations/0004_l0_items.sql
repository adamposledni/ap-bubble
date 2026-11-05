-- L0: every item ingested from an external system (event, mail, task, contact, ...).
-- Common columns serve queries; the source's own representation is kept whole in payload.
CREATE TABLE l0_items (
    id             INTEGER PRIMARY KEY,
    account_id     INTEGER NOT NULL REFERENCES lm_accounts (id),
    source         TEXT    NOT NULL,  -- e.g. 'google_calendar'
    container_id   TEXT    NOT NULL,  -- e.g. calendar id; '' when the source has none
    external_id    TEXT    NOT NULL,  -- id within the container
    kind           TEXT    NOT NULL,  -- 'event', 'mail', 'task', 'contact', ...
    title          TEXT,
    starts_at      TEXT,              -- ISO 8601, UTC; a plain date for all-day items
    ends_at        TEXT,
    deleted        INTEGER NOT NULL DEFAULT 0,  -- deleted or cancelled in the source
    payload        TEXT    NOT NULL,  -- JSON as delivered by the source
    payload_hash   TEXT    NOT NULL,  -- SHA-256 of payload; detects real changes
    changed_run_id INTEGER NOT NULL REFERENCES lm_job_runs (id),  -- change set for the curator
    created_at     TEXT    NOT NULL,  -- ISO 8601, UTC
    changed_at     TEXT    NOT NULL,
    UNIQUE (account_id, source, container_id, external_id)
);

CREATE INDEX ix_l0_items_changed_run_id ON l0_items (changed_run_id);

-- Where each incremental sync left off, per account, source and container.
CREATE TABLE lm_sync_cursors (
    account_id   INTEGER NOT NULL REFERENCES lm_accounts (id),
    source       TEXT    NOT NULL,  -- e.g. 'google_calendar'
    container_id TEXT    NOT NULL,  -- e.g. calendar id; '' when the source has none
    cursor       TEXT    NOT NULL,  -- e.g. Calendar nextSyncToken, Gmail historyId
    updated_at   TEXT    NOT NULL,  -- ISO 8601, UTC
    PRIMARY KEY (account_id, source, container_id)
);

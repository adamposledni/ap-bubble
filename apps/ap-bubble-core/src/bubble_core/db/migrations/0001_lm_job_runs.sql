-- Every job run (ingest, curator, action executor); source of the audit page.
CREATE TABLE lm_job_runs (
    id              INTEGER PRIMARY KEY,
    job_name        TEXT    NOT NULL,  -- e.g. 'ingest.google_calendar'
    scope           TEXT,              -- e.g. account key; NULL for global jobs
    status          TEXT    NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    started_at      TEXT    NOT NULL,  -- ISO 8601, UTC
    finished_at     TEXT,
    items_processed INTEGER NOT NULL DEFAULT 0,
    error           TEXT
);

CREATE INDEX ix_lm_job_runs_job_name_started_at ON lm_job_runs (job_name, started_at);

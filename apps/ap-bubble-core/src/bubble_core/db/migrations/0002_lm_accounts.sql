-- Connected data-source accounts (Google, Microsoft); never the app's own identity.
CREATE TABLE lm_accounts (
    id         INTEGER PRIMARY KEY,
    provider   TEXT    NOT NULL CHECK (provider IN ('google', 'microsoft')),
    email      TEXT    NOT NULL,  -- lower-case
    context    TEXT    NOT NULL CHECK (context IN ('work', 'personal')),
    enabled    INTEGER NOT NULL DEFAULT 1,
    created_at TEXT    NOT NULL,  -- ISO 8601, UTC
    UNIQUE (provider, email)
);

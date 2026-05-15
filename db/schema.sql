-- Operational SQLite schema (BUILD.md Task 0.7).
-- User-owned markdown under `data/` remains canonical per DATA_CONTRACT.md.

PRAGMA foreign_keys = ON;

-- Placeholder migration anchor; LangGraph checkpoints + audit tables land in Task 0.7.
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

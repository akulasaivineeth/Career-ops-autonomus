-- Initial operational schema (arch.D.6). Plain SQLite until Task 5.1 (SQLCipher).
-- ``schema_migrations`` is created by ``db.migrate`` before this script runs.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  jd_id TEXT NOT NULL,
  jd_url TEXT,
  track TEXT CHECK (track IN ('DA', 'MLE', 'DE')),
  score REAL,
  ats_family TEXT,
  status TEXT NOT NULL,
  autonomy_level INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS checkpoints (
  thread_id TEXT NOT NULL,
  checkpoint_id TEXT NOT NULL,
  state BLOB NOT NULL,
  PRIMARY KEY (thread_id, checkpoint_id)
);

CREATE TABLE IF NOT EXISTS actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL REFERENCES runs (run_id) ON DELETE CASCADE,
  ts TEXT NOT NULL,
  agent TEXT NOT NULL,
  tool TEXT NOT NULL,
  args_hash TEXT,
  dom_diff_path TEXT,
  screenshot_path TEXT,
  outcome TEXT
);

CREATE TABLE IF NOT EXISTS approvals (
  run_id TEXT NOT NULL,
  gate TEXT NOT NULL,
  sent_at TEXT,
  decided_at TEXT,
  decision TEXT,
  whatsapp_message_id TEXT,
  PRIMARY KEY (run_id, gate)
);

CREATE TABLE IF NOT EXISTS jd_embeddings (
  jd_id TEXT PRIMARY KEY,
  embedding BLOB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_jd_id ON runs (jd_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs (status);
CREATE INDEX IF NOT EXISTS idx_actions_run_ts ON actions (run_id, ts);
CREATE INDEX IF NOT EXISTS idx_approvals_decision ON approvals (decision);

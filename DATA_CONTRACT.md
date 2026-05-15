# Data contract — user layer vs operational layer

## User-owned markdown (source of truth for humans)

Files under `data/` (for example `applications.md`, `pipeline.md`, `scan-history.tsv`) and curated content under `reports/`, `jds/`, and `cv/` are **human-edited** artifacts.

- Automation **must not** silently rewrite these files without an explicit, reviewable migration (`BUILD.md` tasks such as 1.9).
- Append-only or additive updates should remain **idempotent** and **logged**.

## Operational SQLite (`db/careerops.db`)

LangGraph checkpoints, embeddings, and audit metadata may live in SQLite per **`BUILD.md`**. This database is a **derived operational store**, not a replacement for the markdown contract.

- The database file and WALs are **gitignored**.
- Schema changes go through `db/migrations/` once Task 0.7 lands.

## PDFs and audit media

`output/` and `audit/` are ephemeral artifacts — never commit them.

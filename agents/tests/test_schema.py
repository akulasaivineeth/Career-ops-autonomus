"""SQLite migrations and core tables (BUILD.md Task 0.7)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from db.migrate import apply_migrations


def test_migrate_and_sample_run(tmp_path: Path) -> None:
    db_path = tmp_path / "careerops.db"
    applied = apply_migrations(db_path)
    assert "0001_init.sql" in applied

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "INSERT INTO runs (run_id, jd_id, status, autonomy_level, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))",
        ("run-test-1", "jd-1", "queued", 1),
    )
    assert cur.rowcount == 1
    row = conn.execute(
        "SELECT run_id, jd_id, status FROM runs WHERE run_id = ?", ("run-test-1",)
    ).fetchone()
    assert row is not None
    assert row["jd_id"] == "jd-1"
    conn.close()

    applied_again = apply_migrations(db_path)
    assert applied_again == []

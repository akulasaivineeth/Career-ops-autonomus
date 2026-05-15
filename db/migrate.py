"""
Apply SQL migrations in ``db/migrations/`` order to ``db/careerops.db``.

Idempotent: each file name is recorded in ``schema_migrations``. Safe to re-run.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "careerops.db"


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _applied_names(conn: sqlite3.Connection) -> set[str]:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "name TEXT NOT NULL UNIQUE,"
        "applied_at TEXT NOT NULL DEFAULT (datetime('now'))"
        ")"
    )
    rows = conn.execute("SELECT name FROM schema_migrations").fetchall()
    return {r[0] for r in rows}


def apply_migrations(db_path: Path | None = None) -> list[str]:
    """Run pending migrations; returns list of applied file names."""
    path = db_path or DEFAULT_DB_PATH
    conn = _connect(path)
    applied = _applied_names(conn)
    done: list[str] = []
    try:
        for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            name = sql_file.name
            if name in applied:
                continue
            sql = sql_file.read_text(encoding="utf-8")
            conn.executescript(sql)
            conn.execute("INSERT INTO schema_migrations (name) VALUES (?)", (name,))
            conn.commit()
            done.append(name)
    finally:
        conn.close()
    return done


def main() -> None:
    db_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB_PATH
    applied = apply_migrations(db_arg)
    if applied:
        print("Applied:", ", ".join(applied))
    else:
        print("No pending migrations.")


if __name__ == "__main__":
    main()

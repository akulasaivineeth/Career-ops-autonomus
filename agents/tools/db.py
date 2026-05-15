"""SQLite connection wrapper (plain) + SQLCipher upgrade path (BUILD.md Task 5.1)."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_DB_PATH = Path(__file__).resolve().parents[2] / "db" / "careerops.db"
_USE_CIPHER = os.environ.get("CAREEROPS_SQLCIPHER", "0") == "1"


def get_connection(db_path: Path | None = None) -> Any:
    """
    Return a database connection.

    Uses plain ``sqlite3`` by default.  Set ``CAREEROPS_SQLCIPHER=1`` and ensure
    ``pysqlcipher3`` is installed (``[crypto]`` extra) to enable encryption.
    The encryption key is fetched from Keychain ``careerops.db / encryption_key``.
    """
    path = db_path or _DB_PATH

    if _USE_CIPHER:
        try:
            from pysqlcipher3 import dbapi2 as sqlcipher  # type: ignore[import-untyped]

            from agents.tools.keychain import get_secret

            conn = sqlcipher.connect(str(path), check_same_thread=False)
            key = get_secret("db", "encryption_key")
            if not key:
                raise RuntimeError("SQLCipher key not in Keychain (careerops.db / encryption_key).")
            conn.execute(f"PRAGMA key='{key}'")
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except ImportError:
            log.warning("sqlcipher_not_installed_falling_back_to_plaintext")

    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

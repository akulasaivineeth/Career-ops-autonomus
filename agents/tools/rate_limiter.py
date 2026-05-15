"""
Per-source rate limiter with gaussian inter-arrival and daily caps (BUILD.md Task 3.6).

State is persisted in SQLite so caps survive restarts.
"""

from __future__ import annotations

import random
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import structlog

log = structlog.get_logger(__name__)

_DB_PATH = Path(__file__).resolve().parents[2] / "db" / "careerops.db"

# Default caps (source → (per_hour, per_day))
_DEFAULT_CAPS: dict[str, tuple[int, int]] = {
    "linkedin": (8, 25),
    "indeed": (5, 15),
    "glassdoor": (5, 15),
    "_global": (10, 50),
}
_DEFAULT_CAP = (8, 25)

_QUIET_HOURS = (22, 8)  # 22:00 – 08:00


def _inter_arrival_secs() -> float:
    """Gaussian µ=180s σ=60s clamped to [60, 600]."""
    return max(60.0, min(600.0, random.gauss(180, 60)))


def _in_quiet_hours() -> bool:
    h = datetime.now().hour
    start, end = _QUIET_HOURS
    if start > end:
        return h >= start or h < end
    return start <= h < end


def _window_start_ts(window: str) -> float:
    now = datetime.now()
    if window == "hour":
        return now.replace(minute=0, second=0, microsecond=0).timestamp()
    if window == "day":
        return now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    return 0.0


def _count_since(conn: sqlite3.Connection, source: str, since_ts: float) -> int:
    row = conn.execute(
        "SELECT COUNT(*) FROM actions WHERE agent=? AND ts >= datetime(?, 'unixepoch')",
        (source, since_ts),
    ).fetchone()
    return row[0] if row else 0


class RateLimiter:
    """Check and enforce per-source + global caps."""

    def __init__(self, db_path: Path = _DB_PATH) -> None:
        self._db = db_path

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self._db))

    def can_apply(self, source: str) -> tuple[bool, str]:
        """
        Return ``(True, "")`` if allowed, else ``(False, reason)``.

        Also blocks during quiet hours.
        """
        if _in_quiet_hours():
            return False, "quiet_hours"

        if not self._db.exists():
            return True, ""

        cap_h, cap_d = _DEFAULT_CAPS.get(source, _DEFAULT_CAP)
        glob_h, glob_d = _DEFAULT_CAPS["_global"]

        conn = self._conn()
        try:
            ts_h = _window_start_ts("hour")
            ts_d = _window_start_ts("day")

            src_h = _count_since(conn, source, ts_h)
            src_d = _count_since(conn, source, ts_d)
            all_h = _count_since(conn, "_global", ts_h)
            all_d = _count_since(conn, "_global", ts_d)

            if src_h >= cap_h:
                return False, f"{source}_hourly_cap"
            if src_d >= cap_d:
                return False, f"{source}_daily_cap"
            if all_h >= glob_h:
                return False, "global_hourly_cap"
            if all_d >= glob_d:
                return False, "global_daily_cap"
        finally:
            conn.close()

        return True, ""

    def sleep_inter_arrival(self) -> None:
        """Sleep the gaussian inter-arrival time between applies."""
        delay = _inter_arrival_secs()
        log.info("rate_limiter_sleep", seconds=round(delay, 1))
        time.sleep(delay)

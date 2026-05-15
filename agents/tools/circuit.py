"""Per-adapter circuit breakers — trip on 50% failure rate over rolling 1h (BUILD.md Task 5.3)."""

from __future__ import annotations

import sqlite3
import time
from collections import defaultdict
from pathlib import Path

import structlog

log = structlog.get_logger(__name__)

_DB_PATH = Path(__file__).resolve().parents[2] / "db" / "careerops.db"

_TRIP_THRESHOLD = 0.5
_MIN_ATTEMPTS = 4
_COOLDOWN_SECONDS = 3600


class CircuitBreaker:
    """Track per-adapter failures and trip when threshold exceeded."""

    _tripped_until: dict[str, float] = defaultdict(float)

    def is_open(self, adapter: str) -> bool:
        """Return True if this adapter is currently tripped (open circuit)."""
        return time.time() < self._tripped_until[adapter]

    def record(self, adapter: str, *, success: bool) -> None:
        """Record a result and trip the circuit if threshold exceeded."""
        if not _DB_PATH.exists():
            return

        conn = sqlite3.connect(str(_DB_PATH))
        try:
            window = time.time() - _COOLDOWN_SECONDS
            rows = conn.execute(
                "SELECT outcome FROM actions WHERE agent=? AND ts >= datetime(?, 'unixepoch')",
                (adapter, window),
            ).fetchall()
        finally:
            conn.close()

        recorded = "ok" if success else "fail"
        outcomes = [r[0] for r in rows] + [recorded]
        if len(outcomes) < _MIN_ATTEMPTS:
            return

        fail_rate = outcomes.count("fail") / len(outcomes)
        if fail_rate >= _TRIP_THRESHOLD:
            self._tripped_until[adapter] = time.time() + _COOLDOWN_SECONDS
            log.error("circuit_tripped", adapter=adapter, fail_rate=round(fail_rate, 2))
            try:
                from agents.tools.whatsapp import send_text

                send_text(
                    f"⚠️ career-ops: circuit tripped for {adapter} (fail rate {fail_rate:.0%})"
                )
            except Exception:
                pass

    def reset(self, adapter: str) -> None:
        self._tripped_until[adapter] = 0.0


_CB = CircuitBreaker()

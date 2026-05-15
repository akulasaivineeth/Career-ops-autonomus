"""Circuit breaker tests (BUILD.md Task 5.3)."""

from __future__ import annotations

import time
from pathlib import Path

from agents.tools.circuit import CircuitBreaker


def test_circuit_starts_closed(tmp_path: Path) -> None:
    cb = CircuitBreaker()
    assert cb.is_open("greenhouse") is False


def test_circuit_reset(tmp_path: Path) -> None:
    cb = CircuitBreaker()
    cb._tripped_until["greenhouse"] = time.time() + 9999
    assert cb.is_open("greenhouse") is True
    cb.reset("greenhouse")
    assert cb.is_open("greenhouse") is False


def test_circuit_record_no_db(tmp_path: Path) -> None:
    cb = CircuitBreaker()
    import unittest.mock as mock

    from agents.tools import circuit as c_mod

    with mock.patch.object(c_mod, "_DB_PATH", tmp_path / "nonexistent.db"):
        cb.record("greenhouse", success=False)
    assert cb.is_open("greenhouse") is False

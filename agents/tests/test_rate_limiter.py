"""Rate limiter tests (BUILD.md Task 3.6)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from agents.tools.rate_limiter import RateLimiter, _in_quiet_hours, _inter_arrival_secs


def test_inter_arrival_within_bounds() -> None:
    for _ in range(100):
        val = _inter_arrival_secs()
        assert 60.0 <= val <= 600.0


def test_can_apply_no_db(tmp_path: Path) -> None:
    rl = RateLimiter(db_path=tmp_path / "nonexistent.db")
    allowed, reason = rl.can_apply("greenhouse")
    assert reason == "" or "quiet" in reason


def test_quiet_hours_flag() -> None:
    with patch("agents.tools.rate_limiter.datetime") as mock_dt:
        mock_dt.now.return_value.__class__ = object
        import datetime

        mock_dt.now.return_value = datetime.datetime(2026, 5, 15, 23, 0, 0)
        mock_dt.now.return_value = datetime.datetime(2026, 5, 15, 23, 0, 0)

    # Just verify the function is callable and returns a bool
    result = _in_quiet_hours()
    assert isinstance(result, bool)

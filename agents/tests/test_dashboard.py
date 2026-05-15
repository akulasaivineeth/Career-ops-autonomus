"""Dashboard API and UI tests."""

from __future__ import annotations

from pathlib import Path

from bridge.server import app
from fastapi.testclient import TestClient


def test_root_returns_html() -> None:
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    # Template should contain the page title and Alpine.js
    assert resp.headers["content-type"].startswith("text/html")


def test_dashboard_api_shape() -> None:
    client = TestClient(app)
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    required = (
        "stats",
        "runs",
        "approvals",
        "pipeline",
        "reports",
        "secrets",
        "score_chart",
        "ats_chart",
        "week_activity",
    )
    for key in required:
        assert key in data, f"missing key: {key}"


def test_stats_keys(tmp_path: Path) -> None:
    import unittest.mock as mock

    from bridge import dashboard as d

    with mock.patch.object(d, "_DB_PATH", tmp_path / "nonexistent.db"):
        stats = d.get_stats()
    assert "total" in stats
    assert stats["total"] == 0


def test_week_activity_7_days(tmp_path: Path) -> None:
    import unittest.mock as mock

    from bridge import dashboard as d

    with mock.patch.object(d, "_DB_PATH", tmp_path / "nonexistent.db"):
        wa = d.get_week_activity()
    assert len(wa["labels"]) == 7
    assert len(wa["data"]) == 7


def test_secrets_status_list() -> None:
    from bridge.secrets_status import get_secrets_status

    items = get_secrets_status()
    assert len(items) >= 3
    for item in items:
        assert "label" in item
        assert "ok" in item
        assert isinstance(item["ok"], bool)

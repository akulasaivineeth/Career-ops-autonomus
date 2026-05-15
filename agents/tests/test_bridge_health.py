"""HTTP surface tests for the local control plane (BUILD.md Task 0.6)."""

from __future__ import annotations

from bridge.server import app
from fastapi.testclient import TestClient


def test_health_ok_and_version() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("ok") is True
    assert isinstance(data.get("version"), str)
    assert len(data["version"]) > 0

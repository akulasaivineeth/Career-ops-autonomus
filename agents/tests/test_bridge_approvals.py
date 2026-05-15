"""Bridge approval endpoints (BUILD.md Task 1.7)."""

from __future__ import annotations

import asyncio

from bridge.approvals import APPROVALS_WAITING, resolve_approval
from bridge.server import app
from fastapi.testclient import TestClient


def test_health_shape() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True


def test_approve_rejects_unknown_run() -> None:
    client = TestClient(app)
    resp = client.post("/approve/nonexistent-run-id-xyz")
    assert resp.status_code == 404


def test_reject_rejects_unknown_run() -> None:
    client = TestClient(app)
    resp = client.post("/reject/nonexistent-run-id-xyz")
    assert resp.status_code == 404


def test_whatsapp_inbound_resolves_future() -> None:
    loop = asyncio.new_event_loop()
    fut: asyncio.Future[str] = loop.create_future()
    APPROVALS_WAITING["run-wa-test"] = fut

    client = TestClient(app)
    payload = {
        "entry": [
            {"changes": [{"value": {"messages": [{"text": {"body": "APPROVE"}, "type": "text"}]}}]}
        ]
    }
    resp = client.post("/webhook/whatsapp", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert fut.done()
    assert fut.result() == "approved"

    APPROVALS_WAITING.pop("run-wa-test", None)
    loop.close()


def test_resolve_approval_manually() -> None:
    loop = asyncio.new_event_loop()
    fut: asyncio.Future[str] = loop.create_future()
    APPROVALS_WAITING["run-manual"] = fut

    resolved = resolve_approval("run-manual", "rejected")
    assert resolved is True
    assert fut.result() == "rejected"

    APPROVALS_WAITING.pop("run-manual", None)
    loop.close()

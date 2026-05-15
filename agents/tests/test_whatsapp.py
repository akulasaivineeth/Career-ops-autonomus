"""WhatsApp tool tests — mocked httpx (BUILD.md Task 1.5)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agents.tools import whatsapp as wa_mod


def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WA_PHONE_NUMBER_ID", "12345")
    monkeypatch.setenv("WA_USER_NUMBER", "+19995550001")


def _mock_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(wa_mod, "_token", lambda: "test-token")


def _mock_post(status: int = 200, body: dict | None = None):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = body or {"messages": [{"id": "msg-001"}]}
    resp.raise_for_status = MagicMock()
    return resp


def test_send_text_calls_graph_api(monkeypatch: pytest.MonkeyPatch) -> None:
    _env(monkeypatch)
    _mock_token(monkeypatch)

    with patch("agents.tools.whatsapp.httpx.post", return_value=_mock_post()) as mock_post:
        msg_id = wa_mod.send_text("hello world")

    assert msg_id == "msg-001"
    call_kwargs = mock_post.call_args
    payload = call_kwargs.kwargs["json"]
    assert payload["type"] == "text"
    assert payload["to"] == "+19995550001"
    assert "hello world" in payload["text"]["body"]


def test_send_text_payload_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    _env(monkeypatch)
    _mock_token(monkeypatch)

    captured: list[dict] = []

    def fake_post(url: str, **kwargs: object) -> MagicMock:
        captured.append(kwargs.get("json", {}))
        return _mock_post()

    monkeypatch.setattr(wa_mod.httpx, "post", fake_post)
    wa_mod.send_text("test message")

    assert captured[0]["messaging_product"] == "whatsapp"
    assert captured[0]["type"] == "text"

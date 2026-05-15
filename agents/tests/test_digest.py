"""Digest worker tests (BUILD.md Task 4.4)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from agents.workers import digest as digest_mod
from agents.workers.digest import build_digest


def test_build_digest_no_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(digest_mod, "_DB_PATH", tmp_path / "nonexistent.db")
    msg = build_digest()
    assert "no data" in msg.lower() or "digest" in msg.lower()


def test_build_digest_with_empty_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "careerops.db"
    monkeypatch.setattr(digest_mod, "_DB_PATH", db)

    from db.migrate import apply_migrations

    apply_migrations(db)
    msg = build_digest()
    assert "weekly digest" in msg.lower() or "digest" in msg.lower()


def test_send_digest_calls_whatsapp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(digest_mod, "_DB_PATH", tmp_path / "nonexistent.db")
    sent: list[str] = []

    def fake_send(text: str) -> str:
        sent.append(text)
        return "msg-1"

    import agents.tools.whatsapp as _wa_mod

    with patch.object(_wa_mod, "send_text", fake_send):
        result = digest_mod.send_digest()

    assert result is True
    assert len(sent) == 1

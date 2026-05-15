"""Verifier worker tests — mocked Gmail + no-browser (BUILD.md Task 3.2)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from agents.workers import verifier as v_mod
from agents.workers.verifier import verify_submission


def test_verify_no_email_not_confirmed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v_mod, "_AUDIT_DIR", tmp_path / "audit")
    monkeypatch.setattr(v_mod, "_APPS_MD", tmp_path / "applications.md")

    with patch.object(v_mod, "_gmail_poll", return_value=[]), patch("time.sleep"):
        result = verify_submission("run-v1", "https://example.com", poll_seconds=1)

    assert result["confirmed"] is False
    assert (tmp_path / "audit" / "run-v1" / "verifier" / "evidence.txt").exists()


def test_verify_email_found_confirmed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v_mod, "_AUDIT_DIR", tmp_path / "audit")
    monkeypatch.setattr(v_mod, "_APPS_MD", tmp_path / "applications.md")

    with patch.object(v_mod, "_gmail_poll", return_value=["msg-abc"]):
        result = verify_submission("run-v2", "https://example.com", poll_seconds=1)

    assert result["confirmed"] is True
    assert "msg-abc" in result["evidence"]

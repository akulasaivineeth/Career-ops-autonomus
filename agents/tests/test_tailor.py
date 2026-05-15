"""Tailor worker tests (BUILD.md Task 1.3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agents.workers.tailor import tailor_resume

_JD_TEXT = "ML Engineer role. Python, PyTorch, LLM evaluation, RAG."


def test_tailor_returns_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Tailor returns pdf_path, cover_path, diff_summary without crashing."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()
    (tmp_path / "cv").mkdir()
    (tmp_path / "cv" / "mle.md").write_text("# MLE CV\n- Python bullet")

    result = tailor_resume(_JD_TEXT, "MLE", "run-tailor-1")

    assert "pdf_path" in result
    assert "cover_path" in result
    assert "diff_summary" in result
    assert Path(result["cover_path"]).exists()


def test_tailor_fallback_on_unknown_track(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()
    (tmp_path / "cv").mkdir()

    result = tailor_resume(_JD_TEXT, "UNKNOWN", "run-tailor-2")
    assert "pdf_path" in result

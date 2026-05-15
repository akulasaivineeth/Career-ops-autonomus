"""Scorer worker tests — mocked Anthropic client (BUILD.md Task 1.2)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agents.workers.scorer import score_jd

_JD_FIXTURE = """
Senior ML Engineer

We are looking for an ML Engineer with strong Python and PyTorch experience.
Requirements: 3+ years, Python, PyTorch, MLOps, AWS.
Compensation: $180k-$220k.
Remote OK. No sponsorship required.
"""


def _make_mock_client(track: str = "MLE", score: float = 4.4) -> MagicMock:
    client = MagicMock()
    import json

    payload = json.dumps(
        {
            "track": track,
            "score": score,
            "subscores": {"keyword_match": 0.75, "semantic_sim": 0.80, "experience_fit": 0.90},
            "dimensions": {},
            "rationale": "Good match for MLE role.",
            "kill_signals": [],
            "tailor_keywords": ["Python", "PyTorch", "MLOps"],
        }
    )
    mock_resp = MagicMock()
    mock_resp.content = payload
    client.invoke.return_value = mock_resp
    return client


def test_score_returns_valid_structure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "reports").mkdir()

    result = score_jd(_JD_FIXTURE, run_id="test-1", anthropic_client=_make_mock_client())

    assert "track" in result
    assert result["track"] in {"DA", "MLE", "DE"}
    assert isinstance(result["score"], float)
    assert 1.0 <= result["score"] <= 5.0
    assert "kill_signals" in result
    assert "report_path" in result


def test_kill_signal_auto_rejects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "reports").mkdir()

    jd_with_kill = "Senior Engineer role. US citizen required. Python, AWS."
    result = score_jd(jd_with_kill, run_id="test-kill", anthropic_client=_make_mock_client())
    assert result["status"] == "rejected_auto" or len(result["kill_signals"]) > 0


def test_heuristic_fallback_no_api_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "reports").mkdir()
    monkeypatch.setenv("CAREEROPS_VAULT", "keychain")

    result = score_jd(_JD_FIXTURE, run_id="test-heuristic")

    assert "track" in result
    assert isinstance(result["score"], float)
    assert result["status"] in {"rejected_auto", "score_pass", "score_borderline"}

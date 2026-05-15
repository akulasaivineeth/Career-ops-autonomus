"""Scanner worker tests (BUILD.md Task 3.1)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agents.workers import scanner as scan_mod
from agents.workers.scanner import _jd_hash, _load_seen, scan_greenhouse


def test_jd_hash_consistent() -> None:
    h1 = _jd_hash("acme", "ML Engineer", "Remote")
    h2 = _jd_hash("acme", "ML Engineer", "Remote")
    assert h1 == h2
    assert len(h1) == 16


def test_jd_hash_case_insensitive() -> None:
    h1 = _jd_hash("Acme", "ML Engineer", "remote")
    h2 = _jd_hash("acme", "ml engineer", "Remote")
    assert h1 == h2


def test_load_seen_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scan_mod, "_SCAN_HISTORY", tmp_path / "scan-history.tsv")
    assert _load_seen() == set()


def test_greenhouse_scanner_dedup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scan_mod, "_JDS_DIR", tmp_path / "jds")
    monkeypatch.setattr(scan_mod, "_DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(scan_mod, "_PIPELINE_MD", tmp_path / "data" / "pipeline.md")
    monkeypatch.setattr(scan_mod, "_SCAN_HISTORY", tmp_path / "data" / "scan-history.tsv")

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "jobs": [
            {
                "id": 123,
                "title": "ML Engineer",
                "location": {"name": "Remote"},
                "content": "<p>Job description</p>",
                "absolute_url": "https://boards.greenhouse.io/example/jobs/123",
            }
        ]
    }

    with patch("agents.workers.scanner.httpx.get", return_value=fake_response):
        seen: set[str] = set()
        new_ids = scan_greenhouse(["example-corp"], seen=seen)
        assert len(new_ids) == 1

        # Second call with same seen set → dedup
        new_ids2 = scan_greenhouse(["example-corp"], seen=seen)
        assert len(new_ids2) == 0

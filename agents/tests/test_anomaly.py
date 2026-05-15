"""Anomaly detector tests (BUILD.md Task 4.3)."""

from __future__ import annotations

from agents.workers.anomaly import detect_anomalies


def test_clean_form_low_score() -> None:
    html = "<form><input type='text' name='name'/><input type='email' name='email'/></form>"
    result = detect_anomalies(html)
    assert result["anomaly_score"] < 0.5
    assert isinstance(result["issues"], list)


def test_why_company_question_detected() -> None:
    html = "<label>Why do you want to work here?</label><textarea></textarea>"
    result = detect_anomalies(html)
    assert "custom_why_company" in result["issues"]
    assert result["anomaly_score"] >= 0.25


def test_video_request_detected() -> None:
    html = "<p>Please submit a video response to the following question.</p>"
    result = detect_anomalies(html)
    assert "video_request" in result["issues"]


def test_multiple_textareas_flagged() -> None:
    html = "<textarea></textarea>" * 4
    result = detect_anomalies(html)
    assert any("multiple_free_text" in i for i in result["issues"])

"""Anomaly detector — flags non-standard form fields before apply (BUILD.md Task 4.3)."""

from __future__ import annotations

import re
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_FREE_TEXT_MIN_CHARS = 200

_ANOMALY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"why\s+(do\s+you\s+want|are\s+you\s+interested|this\s+company)", re.I),
        "custom_why_company",
    ),
    (re.compile(r"video\s+(response|upload|intro)", re.I), "video_request"),
    (re.compile(r"work\s+sample|take[\s-]?home\s+(test|project|assignment)", re.I), "work_sample"),
    (re.compile(r"tell\s+us\s+(about\s+yourself|a\s+time)", re.I), "narrative_free_text"),
]


def detect_anomalies(form_html: str) -> dict[str, Any]:
    """
    Inspect rendered form HTML for unusual fields.

    Returns ``{"anomaly_score": float, "issues": [str]}``.
    Score ≥ 0.5 forces HITL even at autonomy level 4.
    """
    issues: list[str] = []
    # Free-text textarea detection
    textareas = re.findall(r"<textarea[^>]*>", form_html, re.I)
    if len(textareas) > 2:
        issues.append(f"multiple_free_text_fields:{len(textareas)}")

    for pattern, label in _ANOMALY_PATTERNS:
        if pattern.search(form_html):
            issues.append(label)

    # Custom screening questions (labels with "?")
    questions = re.findall(r"<label[^>]*>[^<]{20,100}\?</label>", form_html, re.I)
    if questions:
        issues.append(f"custom_screening_questions:{len(questions)}")

    # Score: each issue contributes 0.25 capped at 1.0
    score = min(len(issues) * 0.25, 1.0)
    return {"anomaly_score": round(score, 2), "issues": issues}

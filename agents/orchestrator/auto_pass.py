"""Auto-pass rules for submit gate (BUILD.md Task 4.2, arch.D Phase 4 step 1)."""

from __future__ import annotations

from typing import Any

_SAFE_ATS_FAMILIES = {"greenhouse", "lever", "ashby"}
_SCORE_THRESHOLD = 4.5
_ANOMALY_THRESHOLD = 0.2


def can_auto_submit(state: dict[str, Any]) -> bool:
    """
    Return True only when ALL four conditions hold:
    - score >= 4.5
    - ats_family in {greenhouse, lever, ashby}
    - anomaly_score < 0.2
    - verifier dry-run passes (not implemented until Task 3.2; skipped here)
    """
    score = float(state.get("score") or 0)
    ats = state.get("ats_family", "")
    anomaly = float(state.get("anomaly_score") or 0)

    return score >= _SCORE_THRESHOLD and ats in _SAFE_ATS_FAMILIES and anomaly < _ANOMALY_THRESHOLD

"""Autonomy ladder enforcement (BUILD.md Task 4.1, arch.D Phase 4)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_PROFILE_PATH = Path(__file__).resolve().parents[2] / "config" / "profile.yml"


def load_autonomy_config() -> dict[str, Any]:
    """Load autonomy block from profile.yml."""
    try:
        import yaml  # type: ignore[import-untyped]

        cfg = yaml.safe_load(_PROFILE_PATH.read_text())
        return cfg.get("autonomy", {})
    except Exception:
        return {"level": 1, "rules": {}}


def gate_should_auto_pass(gate: str, state: dict[str, Any]) -> bool:
    """
    Return True when the autonomy level + rules allow skipping HITL for this gate.

    Always returns False for ``final_submit`` at level < 3 to preserve the "no
    auto-submit without explicit consent" safety invariant.
    """
    cfg = load_autonomy_config()
    level = int(cfg.get("level", state.get("autonomy_level", 1)))
    rules: dict[str, str] = cfg.get("rules", {})

    rule_key = {
        "pdf_review": "pdf_review",
        "account_creation": "account_creation",
        "twofa": "twofa",
        "final_submit": "submit_gate",
        "captcha": "captcha_after_3_fail",
    }.get(gate, gate)

    rule_val = rules.get(rule_key, "hitl")

    # Level 0: dry-run — nothing auto-passes
    if level == 0:
        return False

    # final_submit never auto-passes below level 3
    if gate == "final_submit" and level < 3:
        return False

    # Explicit rule overrides
    if rule_val == "auto":
        return True
    if rule_val == "hitl":
        return False
    if rule_val == "auto_if_score_ge_4_5":
        return float(state.get("score") or 0) >= 4.5
    if rule_val == "auto_if_track_stable":
        return level >= 2 and float(state.get("score") or 0) >= 4.3
    if rule_val == "auto_gmail":
        return level >= 2

    return False

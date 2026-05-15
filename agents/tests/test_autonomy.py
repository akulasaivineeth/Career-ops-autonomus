"""Autonomy ladder tests (BUILD.md Task 4.1)."""

from __future__ import annotations

from unittest.mock import patch

from agents.orchestrator.auto_pass import can_auto_submit
from agents.orchestrator.autonomy import gate_should_auto_pass

_SAFE_STATE = {
    "score": 4.6,
    "ats_family": "greenhouse",
    "anomaly_score": 0.0,
    "autonomy_level": 2,
}


def _mock_cfg(level: int, rules: dict) -> dict:
    return {"level": level, "rules": rules}


def test_final_submit_never_auto_below_level3() -> None:
    with patch("agents.orchestrator.autonomy.load_autonomy_config", return_value=_mock_cfg(2, {})):
        assert gate_should_auto_pass("final_submit", _SAFE_STATE) is False


def test_auto_pass_submit_at_level3() -> None:
    with patch(
        "agents.orchestrator.autonomy.load_autonomy_config",
        return_value=_mock_cfg(3, {"submit_gate": "auto_if_score_ge_4_5"}),
    ):
        state = {**_SAFE_STATE, "autonomy_level": 3}
        assert gate_should_auto_pass("final_submit", state) is True


def test_level0_nothing_auto_passes() -> None:
    with patch("agents.orchestrator.autonomy.load_autonomy_config", return_value=_mock_cfg(0, {})):
        for gate in ["pdf_review", "final_submit", "twofa", "account_creation"]:
            assert gate_should_auto_pass(gate, _SAFE_STATE) is False


def test_can_auto_submit_all_conditions_met() -> None:
    assert can_auto_submit(_SAFE_STATE) is True


def test_can_auto_submit_low_score_fails() -> None:
    state = {**_SAFE_STATE, "score": 4.0}
    assert can_auto_submit(state) is False


def test_can_auto_submit_unsafe_ats_fails() -> None:
    state = {**_SAFE_STATE, "ats_family": "workday"}
    assert can_auto_submit(state) is False


def test_can_auto_submit_high_anomaly_fails() -> None:
    state = {**_SAFE_STATE, "anomaly_score": 0.6}
    assert can_auto_submit(state) is False

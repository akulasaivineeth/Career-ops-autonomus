"""
Generic Computer Use fallback adapter — vision-first for arbitrary career pages (BUILD.md Task 2.7).

Hard cap: max 8 vision steps per page before escalating to HITL.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any

import structlog

from agents.adapters.base import ATSAdapter

log = structlog.get_logger(__name__)

_MAX_CU_STEPS = 8


class GenericAdapter(ATSAdapter):
    def run_sync(
        self,
        page: Any,
        *,
        pdf_path: str | None,
        cover_path: str | None,
        run_id: str,
        approval_callback: Callable[[str, str, str], str],
        screenshot_fn: Callable[[str], str],
    ) -> dict[str, Any]:
        from agents.tools.computer_use import run_computer_use_step

        steps_taken = 0
        while steps_taken < _MAX_CU_STEPS:
            shot = screenshot_fn(f"cu_step_{steps_taken}")
            action = run_computer_use_step(
                page,
                "Fill in the next required form field for the job application. "
                "If you see a Submit button and all fields are filled, call DONE.",
                shot,
                run_id,
            )
            steps_taken += 1
            if "done" in action.lower() or "submit" in action.lower():
                break

        if steps_taken >= _MAX_CU_STEPS:
            log.warning("generic_cu_max_steps_reached", run_id=run_id)
            shot = screenshot_fn("cu_anomaly")
            decision = approval_callback(
                "anomaly",
                shot,
                f"Generic form: reached max vision steps ({_MAX_CU_STEPS}). Manual review needed.",
            )
            if decision != "approved":
                return {"submitted": False, "reason": "anomaly_escalation"}

        shot = screenshot_fn("pre_submit")
        decision = approval_callback("final_submit", shot, f"Generic form ready (run {run_id})")
        if decision == "approved":
            with contextlib.suppress(Exception):
                page.click("button[type='submit'], input[type='submit']")
            return {"submitted": True}
        return {"submitted": False, "reason": "user_rejected"}

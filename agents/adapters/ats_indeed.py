"""Indeed Easy Apply adapter (BUILD.md Task 2.4). Daily cap ≤15."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any

import structlog

from agents.adapters.base import ATSAdapter

log = structlog.get_logger(__name__)


class IndeedAdapter(ATSAdapter):
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
        try:
            if pdf_path:
                with contextlib.suppress(Exception):
                    page.set_input_files("input[type='file']", pdf_path)
            shot = screenshot_fn("pre_submit")
            decision = approval_callback("final_submit", shot, f"Indeed form ready (run {run_id})")
            if decision == "approved":
                page.click("button[aria-label='Continue applying']")
                return {"submitted": True}
            return {"submitted": False, "reason": "user_rejected"}
        except Exception as exc:
            log.error("indeed_adapter_error", run_id=run_id, error=str(exc))
            return {"submitted": False, "error": str(exc)}

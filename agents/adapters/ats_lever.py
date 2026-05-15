"""Lever ATS adapter (BUILD.md Task 2.1)."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any

import structlog

from agents.adapters.base import ATSAdapter

log = structlog.get_logger(__name__)


class LeverAdapter(ATSAdapter):
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
        profile = self._load_profile()
        identity = profile.get("identity", {})
        try:
            self._fill_personal(page, identity)
            if pdf_path:
                page.set_input_files("input[type='file']", pdf_path)
            shot = screenshot_fn("pre_submit")
            decision = approval_callback("final_submit", shot, f"Lever form ready (run {run_id})")
            if decision == "approved":
                page.click("button[type='submit']")
                return {"submitted": True}
            return {"submitted": False, "reason": "user_rejected"}
        except Exception as exc:
            log.error("lever_adapter_error", run_id=run_id, error=str(exc))
            return {"submitted": False, "error": str(exc)}

    def _fill_personal(self, page: Any, identity: dict[str, Any]) -> None:
        for sel, key in [
            ("input[name='name']", "display_name"),
            ("input[name='email']", "email"),
            ("input[name='phone']", "phone"),
        ]:
            val = identity.get(key, "")
            if val:
                with contextlib.suppress(Exception):
                    page.fill(sel, val)

"""Workday multi-page wizard adapter (BUILD.md Task 2.3)."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any

import structlog

from agents.adapters.base import ATSAdapter

log = structlog.get_logger(__name__)

_WIZARD_STAGES = [
    "My Information",
    "My Experience",
    "Application Questions",
    "Voluntary Disclosures",
    "Review",
]


class WorkdayAdapter(ATSAdapter):
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
            self._fill_my_information(page, identity)
            self._fill_my_experience(page, pdf_path)
            self._advance_wizard(page)

            shot = screenshot_fn("pre_submit")
            decision = approval_callback("final_submit", shot, f"Workday form ready (run {run_id})")
            if decision == "approved":
                try:
                    page.click("[data-automation-id='bottom-navigation-next-btn']")
                except Exception:
                    page.click("button[type='submit']")
                return {"submitted": True}
            return {"submitted": False, "reason": "user_rejected"}
        except Exception as exc:
            log.error("workday_adapter_error", run_id=run_id, error=str(exc))
            return {"submitted": False, "error": str(exc)}

    def _fill_my_information(self, page: Any, identity: dict[str, Any]) -> None:
        mapping = {
            "[data-automation-id='legalNameSection_firstName']": identity.get("first_name", ""),
            "[data-automation-id='legalNameSection_lastName']": identity.get("last_name", ""),
            "[data-automation-id='email']": identity.get("email", ""),
        }
        for sel, val in mapping.items():
            if val:
                with contextlib.suppress(Exception):
                    page.fill(sel, val)

    def _fill_my_experience(self, page: Any, pdf_path: str | None) -> None:
        if pdf_path:
            with contextlib.suppress(Exception):
                page.set_input_files("[data-automation-id='file-upload-input-ref']", pdf_path)

    def _advance_wizard(self, page: Any) -> None:
        with contextlib.suppress(Exception):
            page.click("[data-automation-id='bottom-navigation-next-btn']")

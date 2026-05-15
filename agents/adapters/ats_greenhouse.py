"""Greenhouse ATS form adapter (BUILD.md Task 1.4)."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any

import structlog

from agents.adapters.base import ATSAdapter

log = structlog.get_logger(__name__)


class GreenhouseAdapter(ATSAdapter):
    """
    Fills Greenhouse application forms using stable CSS selectors.

    Never clicks submit — calls ``approval_callback("final_submit", ...)`` instead.
    """

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
                self._upload_resume(page, pdf_path)
            if cover_path:
                self._fill_cover(page, cover_path)
            self._handle_eeo(page, profile)

            shot = screenshot_fn("pre_submit")
            decision = approval_callback(
                "final_submit",
                shot,
                f"Greenhouse form ready for submission (run {run_id}).",
            )
            if decision == "approved":
                self._click_submit(page)
                return {"submitted": True}
            return {"submitted": False, "reason": "user_rejected"}

        except Exception as exc:
            log.error("greenhouse_adapter_error", run_id=run_id, error=str(exc))
            return {"submitted": False, "error": str(exc)}

    def _fill_personal(self, page: Any, identity: dict[str, Any]) -> None:
        _try_fill(page, "#first_name", identity.get("first_name", ""))
        _try_fill(page, "#last_name", identity.get("last_name", ""))
        _try_fill(page, "#email", identity.get("email", ""))
        _try_fill(page, "#phone", identity.get("phone", ""))

    def _upload_resume(self, page: Any, pdf_path: str) -> None:
        try:
            page.set_input_files("#resume", pdf_path)
        except Exception as exc:
            log.warning("greenhouse_resume_upload_failed", error=str(exc))

    def _fill_cover(self, page: Any, cover_path: str) -> None:
        try:
            from pathlib import Path

            cover_text = Path(cover_path).read_text(encoding="utf-8") if cover_path else ""
            _try_fill(page, "#cover_letter", cover_text)
        except Exception as exc:
            log.warning("greenhouse_cover_fill_failed", error=str(exc))

    def _handle_eeo(self, page: Any, profile: dict[str, Any]) -> None:
        pass  # EEO dropdowns differ per form; handled by anomaly detector escalation

    def _click_submit(self, page: Any) -> None:
        try:
            page.click("#submit_app")
        except Exception:
            page.click("button[type='submit']")


def _try_fill(page: Any, selector: str, value: str) -> None:
    if not value:
        return
    with contextlib.suppress(Exception):
        page.fill(selector, value)

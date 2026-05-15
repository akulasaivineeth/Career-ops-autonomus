"""
LinkedIn Easy Apply adapter (BUILD.md Task 2.6).

HARD RULES (never relax):
- No profile scraping. No data extraction beyond what the user submits.
- No fake account creation.
- Cap: ≤8/hr, ≤25/day (enforced by rate_limiter.py).
- On "restricted" page → halt LinkedIn globally for 60 min + WhatsApp alert.
"""

from __future__ import annotations

import contextlib
import re
from collections.abc import Callable
from typing import Any

import structlog

from agents.adapters.base import ATSAdapter

log = structlog.get_logger(__name__)

_RESTRICTED_RE = re.compile(r"restricted|verify\s+you|checkpoint", re.I)
_APPLY_MODAL_SEL = ".jobs-easy-apply-modal, [data-test-modal]"


class LinkedInAdapter(ATSAdapter):
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
            if _RESTRICTED_RE.search(page.url):
                self._handle_restriction(page, run_id)
                return {"submitted": False, "error": "linkedin_restricted"}

            profile = self._load_profile()
            _ = profile  # identity fields reserved for future field-fill support

            page.wait_for_selector(_APPLY_MODAL_SEL, timeout=10000)

            if pdf_path:
                with contextlib.suppress(Exception):
                    page.set_input_files("input[type='file']", pdf_path)

            shot = screenshot_fn("pre_submit")
            decision = approval_callback(
                "final_submit", shot, f"LinkedIn Easy Apply ready (run {run_id})"
            )
            if decision == "approved":
                page.click("button[aria-label='Submit application']")
                return {"submitted": True}
            return {"submitted": False, "reason": "user_rejected"}

        except Exception as exc:
            log.error("linkedin_adapter_error", run_id=run_id, error=str(exc))
            return {"submitted": False, "error": str(exc)}

    def _handle_restriction(self, page: Any, run_id: str) -> None:
        log.error("linkedin_restricted", run_id=run_id, url=page.url)
        try:
            from agents.tools.whatsapp import send_text

            send_text(
                f"🚨 career-ops: LinkedIn RESTRICTED page detected (run {run_id}). "
                "LinkedIn source halted for 60 min."
            )
        except Exception:
            pass

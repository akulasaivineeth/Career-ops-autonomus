"""Applier worker — drives browser to fill and submit job applications (BUILD.md Task 1.6)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import structlog

log = structlog.get_logger(__name__)


def drive_application(
    jd_url: str,
    pdf_path: str | None,
    cover_path: str | None,
    run_id: str,
    *,
    approval_callback: Callable[[str, str, str], str],
) -> dict[str, Any]:
    """
    Drive one application end-to-end.

    Calls ``approval_callback(gate_kind, screenshot_path, summary)`` before every
    risky action; returns only after human approval is received.

    Returns ``{"ats_family": str, "submitted": bool}``.
    """
    from agents.tools.browser_harness import apply_to_url

    return apply_to_url(
        jd_url,
        pdf_path=pdf_path,
        cover_path=cover_path,
        run_id=run_id,
        approval_callback=approval_callback,
    )

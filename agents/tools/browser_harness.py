"""
Playwright + Computer Use browser harness (BUILD.md Task 1.6, arch.G.5).

All submit actions go through ``approval_callback`` before clicking.
"""

from __future__ import annotations

import os
import random
import re
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_BROWSER_CTX_BASE = Path(
    os.environ.get(
        "CAREEROPS_BROWSER_CTX_DIR",
        Path.home() / "Library" / "Application Support" / "career-ops" / "browser",
    )
)
_AUDIT_DIR = Path(__file__).resolve().parents[2] / "audit"

_ATS_PATTERNS: dict[str, re.Pattern[str]] = {
    "greenhouse": re.compile(r"greenhouse\.io|boards\.greenhouse", re.I),
    "lever": re.compile(r"jobs\.lever\.co|lever\.co/", re.I),
    "ashby": re.compile(r"ashbyhq\.com", re.I),
    "workday": re.compile(r"myworkdayjobs\.com|workday\.com", re.I),
    "linkedin": re.compile(r"linkedin\.com/jobs", re.I),
    "indeed": re.compile(r"indeed\.com", re.I),
    "glassdoor": re.compile(r"glassdoor\.com", re.I),
    "wellfound": re.compile(r"wellfound\.com|angel\.co", re.I),
}


def detect_ats(url: str) -> str:
    """Return ATS family string from URL pattern, or ``'generic'``."""
    for family, pattern in _ATS_PATTERNS.items():
        if pattern.search(url):
            return family
    return "generic"


def _ctx_dir(site_key: str) -> Path:
    path = _BROWSER_CTX_BASE / site_key
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    return path


def screenshot(page: Any, label: str, run_id: str) -> str:
    """Save a screenshot to ``audit/{run_id}/{ts}-{label}.png`` and return the path."""
    ev_dir = _AUDIT_DIR / run_id
    ev_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    path = ev_dir / f"{ts}-{label}.png"
    try:
        page.screenshot(path=str(path))
    except Exception as exc:
        log.warning("screenshot_failed", label=label, error=str(exc))
    return str(path)


def human_type(page: Any, selector: str, text: str) -> None:
    """Type ``text`` into ``selector`` with variable human-like delay."""
    page.click(selector)
    for char in text:
        page.type(selector, char)
        delay = random.uniform(0.07, 0.13)
        time.sleep(delay)
    time.sleep(random.uniform(0.4, 0.8))


def computer_use_step(page: Any, instruction: str, run_id: str) -> str:
    """
    Single vision-driven step using Anthropic Computer Use (claude-sonnet-4-5).

    Returns the model's chosen action description.
    """
    from agents.tools.computer_use import run_computer_use_step

    shot_path = screenshot(page, "cu_before", run_id)
    return run_computer_use_step(page, instruction, shot_path, run_id)


def apply_to_url(
    jd_url: str,
    *,
    pdf_path: str | None,
    cover_path: str | None,
    run_id: str,
    approval_callback: Callable[[str, str, str], str],
) -> dict[str, Any]:
    """
    Drive a full application to ``jd_url``.

    Calls ``approval_callback(gate_kind, screenshot_path, summary)`` before
    risky actions. Never submits without ``"approved"`` response.
    """
    ats_family = detect_ats(jd_url)
    log.info("apply_start", jd_url=jd_url, ats_family=ats_family, run_id=run_id)

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            ctx_dir = _ctx_dir(ats_family)
            browser = pw.chromium.launch(headless=False, channel="chrome")
            context = browser.new_context(
                storage_state=str(ctx_dir / "state.json")
                if (ctx_dir / "state.json").exists()
                else None
            )
            try:
                from playwright_stealth import stealth_sync  # type: ignore[import-untyped]

                page = context.new_page()
                stealth_sync(page)
            except ImportError:
                page = context.new_page()

            page.goto(jd_url, wait_until="networkidle")
            screenshot(page, "landing", run_id)

            # Dispatch to ATS-specific adapter
            from agents.adapters import REGISTRY

            adapter_cls = REGISTRY.get(ats_family) or REGISTRY["generic"]
            result = adapter_cls().run_sync(
                page,
                pdf_path=pdf_path,
                cover_path=cover_path,
                run_id=run_id,
                approval_callback=approval_callback,
                screenshot_fn=lambda lbl: screenshot(page, lbl, run_id),
            )

            # Save updated session state
            context.storage_state(path=str(ctx_dir / "state.json"))
            context.close()
            browser.close()
            return {"ats_family": ats_family, **result}

    except Exception as exc:
        log.error("apply_failed", jd_url=jd_url, run_id=run_id, error=str(exc))
        return {"ats_family": ats_family, "submitted": False, "error": str(exc)}

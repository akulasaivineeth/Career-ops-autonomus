"""Cookie / session healthcheck — verifies logins before scheduled apply (BUILD.md Task 5.4)."""

from __future__ import annotations

import os
from pathlib import Path

import structlog

log = structlog.get_logger(__name__)

_BROWSER_CTX_BASE = Path(
    os.environ.get(
        "CAREEROPS_BROWSER_CTX_DIR",
        Path.home() / "Library" / "Application Support" / "career-ops" / "browser",
    )
)

_LOGIN_REDIRECT_PATTERNS = [
    "login",
    "signin",
    "sign-in",
    "auth",
    "session-expired",
]

_CHECKED_SITES = ["greenhouse", "lever", "linkedin", "workday"]


def check_session(site_key: str) -> bool:
    """
    Open the persistent browser context for ``site_key`` and verify login.

    Returns True if session is active, False if expired.
    """
    ctx_dir = _BROWSER_CTX_BASE / site_key
    state_path = ctx_dir / "state.json"
    if not state_path.exists():
        log.info("session_no_state", site=site_key)
        return False

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, channel="chrome")
            context = browser.new_context(storage_state=str(state_path))
            page = context.new_page()

            _site_url = _ping_urls().get(site_key)
            if not _site_url:
                context.close()
                browser.close()
                return True  # no URL to check — assume OK

            page.goto(_site_url, wait_until="networkidle", timeout=15000)
            current_url = page.url.lower()
            expired = any(p in current_url for p in _LOGIN_REDIRECT_PATTERNS)

            context.close()
            browser.close()

            if expired:
                log.warning("session_expired", site=site_key)
                _alert_user(site_key)
            return not expired

    except Exception as exc:
        log.error("session_check_failed", site=site_key, error=str(exc))
        return False


def _ping_urls() -> dict[str, str]:
    return {
        "greenhouse": "https://app.greenhouse.io",
        "lever": "https://hire.lever.co",
        "linkedin": "https://www.linkedin.com/jobs",
    }


def _alert_user(site_key: str) -> None:
    try:
        from agents.tools.whatsapp import send_text

        send_text(
            f"⚠️ career-ops: {site_key} session expired. "
            "Please log in again before the next scheduled apply."
        )
    except Exception:
        pass


def run_all_checks() -> dict[str, bool]:
    """Run session checks for all known sites. Returns {site: is_healthy}."""
    results: dict[str, bool] = {}
    for site in _CHECKED_SITES:
        results[site] = check_session(site)
    return results

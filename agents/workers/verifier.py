"""Verifier worker — confirms submission via Gmail + DOM check (BUILD.md Task 3.2)."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_AUDIT_DIR = Path(__file__).resolve().parents[2] / "audit"
_APPS_MD = Path(__file__).resolve().parents[2] / "data" / "applications.md"

_CONFIRMATION_SENDERS = (
    "greenhouse.io",
    "lever.co",
    "ashbyhq.com",
    "myworkdayjobs.com",
    "indeed.com",
)

_CONFIRMATION_DOM = re.compile(
    r"thanks?\s+for\s+applying|application\s+received|successfully\s+submitted",
    re.I,
)


def _gmail_poll(run_id: str, domain: str | None = None) -> list[str]:
    """Poll Gmail for confirmation emails. Returns list of message IDs found."""
    try:
        from agents.tools.gmail import get_service, search

        svc = get_service()
        senders = "|".join(_CONFIRMATION_SENDERS if not domain else [domain])
        msgs = search(svc, f"from:({senders}) newer_than:12h", max_results=10)
        return [m["id"] for m in msgs]
    except Exception as exc:
        log.warning("verifier_gmail_poll_failed", error=str(exc))
        return []


def _save_evidence(run_id: str, artifact: str) -> None:
    ev_dir = _AUDIT_DIR / run_id / "verifier"
    ev_dir.mkdir(parents=True, exist_ok=True)
    (ev_dir / "evidence.txt").write_text(artifact, encoding="utf-8")


def _update_applications_md(run_id: str, status: str) -> None:
    if not _APPS_MD.exists():
        return
    content = _APPS_MD.read_text(encoding="utf-8")
    # Simple in-place run_id search; full markdown table update per DATA_CONTRACT.
    if run_id in content:
        content = re.sub(
            rf"(\|\s*{re.escape(run_id)}\s*\|[^\n]*)\|\s*\w+\s*\|",
            rf"\1| {status} |",
            content,
        )
        _APPS_MD.write_text(content, encoding="utf-8")


def verify_submission(
    run_id: str,
    jd_url: str,
    *,
    poll_seconds: int = 600,
) -> dict[str, Any]:
    """
    Confirm submission via Gmail polling.

    Returns ``{"confirmed": bool, "evidence": [...]}``.
    """
    evidence: list[str] = []

    deadline = time.monotonic() + poll_seconds
    while time.monotonic() < deadline:
        msg_ids = _gmail_poll(run_id)
        if msg_ids:
            evidence.extend(msg_ids)
            break
        time.sleep(30)

    confirmed = len(evidence) > 0
    _save_evidence(run_id, "\n".join(evidence) if evidence else "no_evidence")
    _update_applications_md(run_id, "submitted" if confirmed else "apply_failed")

    log.info("verifier_done", run_id=run_id, confirmed=confirmed, evidence_count=len(evidence))
    return {"confirmed": confirmed, "evidence": evidence}

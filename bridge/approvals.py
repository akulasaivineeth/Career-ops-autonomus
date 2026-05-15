"""
HITL approval FSM for the bridge (BUILD.md Task 1.7, arch.E.4, arch.G.2).

``request_approval`` blocks asyncio until the user replies or timeout.
Reply arrives via POST /webhook/whatsapp, POST /approve/{run_id}, or POST /reject/{run_id}.
"""

from __future__ import annotations

import asyncio
import sqlite3
import time
from pathlib import Path
from typing import Literal

import structlog

log = structlog.get_logger(__name__)

_DB_PATH = Path(__file__).resolve().parents[1] / "db" / "careerops.db"

# In-memory map: run_id → asyncio.Future
APPROVALS_WAITING: dict[str, asyncio.Future[str]] = {}


async def request_approval(
    run_id: str,
    gate: str,
    screenshot_path: str,
    summary: str,
    *,
    timeout_seconds: int = 1800,
) -> Literal["approved", "rejected", "timeout"]:
    """
    Send WhatsApp notification and await user decision.

    Returns ``"approved"``, ``"rejected"``, or ``"timeout"``.
    """
    _record_pending(run_id, gate, screenshot_path)

    try:
        from agents.tools.whatsapp import send_image_with_caption, send_text

        msg = (
            f"🤖 career-ops gate: *{gate}*\n"
            f"run: `{run_id}`\n\n"
            f"{summary[:800]}\n\n"
            f"Reply: *APPROVE* or *REJECT*"
        )
        if screenshot_path and Path(screenshot_path).exists():
            msg_id = send_image_with_caption(screenshot_path, msg)
        else:
            msg_id = send_text(msg)
        _update_msg_id(run_id, gate, msg_id)
    except Exception as exc:
        log.warning("approval_whatsapp_send_failed", run_id=run_id, gate=gate, error=str(exc))

    loop = asyncio.get_event_loop()
    fut: asyncio.Future[str] = loop.create_future()
    APPROVALS_WAITING[run_id] = fut

    try:
        decision: str = await asyncio.wait_for(fut, timeout=float(timeout_seconds))
    except TimeoutError:
        decision = "timeout"
        log.warning("approval_timeout", run_id=run_id, gate=gate)
        try:
            from agents.tools.whatsapp import send_text

            send_text(
                f"⏰ Timeout on run `{run_id}` ({gate}). Paused — reply *RESUME* or *CANCEL*."
            )
        except Exception:
            pass
        _update_decision(run_id, gate, "timeout")
        return "timeout"  # type: ignore[return-value]
    finally:
        APPROVALS_WAITING.pop(run_id, None)

    _update_decision(run_id, gate, decision)
    return decision  # type: ignore[return-value]


def resolve_approval(run_id: str, decision: str) -> bool:
    """Resolve a pending future from an inbound webhook or manual override."""
    fut = APPROVALS_WAITING.get(run_id)
    if fut is None or fut.done():
        return False
    fut.set_result(decision)
    return True


def restore_on_startup() -> None:
    """On server restart mark all pending approvals as paused (best-effort)."""
    if not _DB_PATH.exists():
        return
    conn = sqlite3.connect(str(_DB_PATH))
    try:
        conn.execute(
            "UPDATE approvals SET decision='paused' WHERE decision IS NULL AND sent_at IS NOT NULL"
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def _record_pending(run_id: str, gate: str, screenshot_path: str) -> None:
    if not _DB_PATH.exists():
        return
    conn = sqlite3.connect(str(_DB_PATH))
    try:
        conn.execute(
            "INSERT OR IGNORE INTO approvals (run_id, gate, sent_at) VALUES (?, ?, ?)",
            (run_id, gate, time.strftime("%Y-%m-%dT%H:%M:%S")),
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def _update_msg_id(run_id: str, gate: str, msg_id: str) -> None:
    if not _DB_PATH.exists():
        return
    conn = sqlite3.connect(str(_DB_PATH))
    try:
        conn.execute(
            "UPDATE approvals SET whatsapp_message_id=? WHERE run_id=? AND gate=?",
            (msg_id, run_id, gate),
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def _update_decision(run_id: str, gate: str, decision: str) -> None:
    if not _DB_PATH.exists():
        return
    conn = sqlite3.connect(str(_DB_PATH))
    try:
        conn.execute(
            "UPDATE approvals SET decided_at=?, decision=? WHERE run_id=? AND gate=?",
            (time.strftime("%Y-%m-%dT%H:%M:%S"), decision, run_id, gate),
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

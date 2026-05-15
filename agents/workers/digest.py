"""Weekly WhatsApp digest — sent Sunday 18:00 local (BUILD.md Task 4.4)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_DB_PATH = Path(__file__).resolve().parents[2] / "db" / "careerops.db"


def _query_week_stats(conn: sqlite3.Connection) -> dict[str, Any]:
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    rows = conn.execute(
        "SELECT status, COUNT(*) as n FROM runs WHERE created_at >= ? GROUP BY status",
        (week_ago,),
    ).fetchall()
    stats: dict[str, int] = {}
    for status, n in rows:
        stats[status] = n
    submitted = stats.get("submitted", 0)
    total = sum(stats.values())
    return {
        "total_this_week": total,
        "submitted": submitted,
        "response_rate": round(submitted / total * 100, 1) if total else 0.0,
        "by_status": stats,
    }


def build_digest() -> str:
    """Build the weekly digest message text."""
    if not _DB_PATH.exists():
        return "career-ops weekly digest: no data (DB not found)."

    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    stats = _query_week_stats(conn)
    conn.close()

    date_str = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"📊 career-ops weekly digest — {date_str}",
        "",
        f"✅ Applied this week: {stats['submitted']} / {stats['total_this_week']}",
        f"📬 Response rate: {stats['response_rate']}%",
        "",
        "Status breakdown:",
    ]
    for status, count in stats.get("by_status", {}).items():
        lines.append(f"  {status}: {count}")

    return "\n".join(lines)


def send_digest() -> bool:
    """Build and send the weekly digest via WhatsApp. Returns True on success."""
    try:
        import agents.tools.whatsapp as _wa

        msg = build_digest()
        _wa.send_text(msg)
        log.info("digest_sent")
        return True
    except Exception as exc:
        log.error("digest_send_failed", error=str(exc))
        return False

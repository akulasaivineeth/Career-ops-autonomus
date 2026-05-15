"""
HTTP control plane for the LangGraph stack (BUILD.md Tasks 0.6 + 1.7).

Binds loopback only. Endpoints:
  GET  /                    → Dashboard UI
  GET  /api/dashboard       → Dashboard JSON data
  GET  /health
  POST /run
  GET  /state/{run_id}
  POST /internal/request_approval
  GET  /webhook/whatsapp    (Meta verification)
  POST /webhook/whatsapp    (inbound replies)
  POST /approve/{run_id}
  POST /reject/{run_id}
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from bridge.approvals import (
    APPROVALS_WAITING,
    request_approval,
    resolve_approval,
    restore_on_startup,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_VERIFY_TOKEN = os.environ.get("WA_WEBHOOK_VERIFY_TOKEN", "")
_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


def _git_short_sha() -> str:
    if sha := os.environ.get("GITHUB_SHA"):
        return sha[:7]
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    except OSError:
        pass
    return "dev"


app = FastAPI(
    title="Career Ops Bridge",
    version="0.1.0",
    description="Local HITL + status API for the autonomous applier (see BUILD.md).",
    on_startup=[restore_on_startup],  # type: ignore[arg-type]
)


# ---------------------------------------------------------------------------
# Dashboard UI
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_ui(request: Request) -> HTMLResponse:
    """Serve the single-page dashboard."""
    db_path = _REPO_ROOT / "db" / "careerops.db"
    import sqlite3

    db_tables = 0
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            db_tables = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
            conn.close()
        except Exception:
            pass

    html = _TEMPLATES.get_template("dashboard.html").render(
        version=_git_short_sha(), db_tables=db_tables
    )
    return HTMLResponse(html)


@app.get("/api/dashboard")
async def dashboard_data() -> dict:
    """Return all dashboard data as JSON for the Alpine.js frontend."""
    from bridge.dashboard import (
        get_ats_chart_data,
        get_pending_approvals,
        get_pipeline,
        get_recent_runs,
        get_reports,
        get_score_chart_data,
        get_stats,
        get_week_activity,
    )
    from bridge.secrets_status import get_secrets_status

    return {
        "stats": get_stats(),
        "runs": get_recent_runs(50),
        "approvals": get_pending_approvals(),
        "pipeline": get_pipeline(100),
        "reports": get_reports(30),
        "secrets": get_secrets_status(),
        "score_chart": get_score_chart_data(),
        "ats_chart": get_ats_chart_data(),
        "week_activity": get_week_activity(),
    }


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict[str, bool | str]:
    """Liveness: ``ok`` + ``version`` (git short SHA when available). BUILD.md Task 0.6."""
    return {"ok": True, "version": _git_short_sha()}


# ---------------------------------------------------------------------------
# Run management
# ---------------------------------------------------------------------------


class RunRequest(BaseModel):
    jd_id: str
    jd_url: str
    jd_text: str = ""
    autonomy_level: int = 1


@app.post("/run")
async def start_run(req: RunRequest, background: BackgroundTasks) -> dict[str, str]:
    """Launch an orchestrator graph run. Returns ``{run_id}``."""
    from nanoid import generate as nanoid

    run_id = f"run-{nanoid(size=8)}"
    background.add_task(_run_graph, run_id, req)
    return {"run_id": run_id}


async def _run_graph(run_id: str, req: RunRequest) -> None:
    try:
        from agents.orchestrator.graph import build_graph
        from agents.orchestrator.state import AppState
        from langgraph.checkpoint.sqlite import SqliteSaver

        db_path = _REPO_ROOT / "db" / "careerops.db"
        with SqliteSaver.from_conn_string(str(db_path)) as saver:
            graph = build_graph(saver)
            state: AppState = {
                "run_id": run_id,
                "jd_id": req.jd_id,
                "jd_url": req.jd_url,
                "jd_text": req.jd_text,
                "track": None,
                "score": None,
                "report_path": None,
                "pdf_path": None,
                "cover_path": None,
                "ats_family": None,
                "autonomy_level": req.autonomy_level,
                "errors": [],
                "gate_pending": None,
                "screenshot_path": None,
            }
            graph.invoke(state, {"configurable": {"thread_id": run_id}})
    except Exception as exc:
        import structlog

        structlog.get_logger(__name__).error("run_graph_failed", run_id=run_id, error=str(exc))


@app.get("/state/{run_id}")
def get_state(run_id: str) -> dict[str, object]:
    """Return latest checkpoint state for ``run_id``."""
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver

        db_path = _REPO_ROOT / "db" / "careerops.db"
        with SqliteSaver.from_conn_string(str(db_path)) as saver:
            cfg = {"configurable": {"thread_id": run_id}}
            snap = saver.get(cfg)
            if snap is None:
                raise HTTPException(status_code=404, detail="run_id not found")
            return {"run_id": run_id, "state": snap.channel_values if snap else {}}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# HITL approval
# ---------------------------------------------------------------------------


class ApprovalRequest(BaseModel):
    run_id: str
    gate: str
    screenshot_path: str = ""
    summary: str = ""
    timeout_seconds: int = 1800


@app.post("/internal/request_approval")
async def api_request_approval(req: ApprovalRequest) -> dict[str, str]:
    """Orchestrator calls this to block until user approves or timeout."""
    decision = await request_approval(
        req.run_id,
        req.gate,
        req.screenshot_path,
        req.summary,
        timeout_seconds=req.timeout_seconds,
    )
    return {"decision": decision}


@app.post("/approve/{run_id}")
async def approve(run_id: str) -> dict[str, str]:
    """Manual CLI / TUI override to approve a pending gate."""
    if resolve_approval(run_id, "approved"):
        return {"status": "resolved", "decision": "approved"}
    raise HTTPException(status_code=404, detail="No pending approval for this run_id")


@app.post("/reject/{run_id}")
async def reject(run_id: str) -> dict[str, str]:
    """Manual CLI / TUI override to reject a pending gate."""
    if resolve_approval(run_id, "rejected"):
        return {"status": "resolved", "decision": "rejected"}
    raise HTTPException(status_code=404, detail="No pending approval for this run_id")


# ---------------------------------------------------------------------------
# WhatsApp webhook
# ---------------------------------------------------------------------------


@app.get("/webhook/whatsapp")
async def whatsapp_verify(
    request: Request,
) -> object:
    """Meta webhook verification (hub.mode / hub.verify_token / hub.challenge)."""
    params = dict(request.query_params)
    mode = params.get("hub.mode", "")
    token = params.get("hub.verify_token", "")
    challenge = params.get("hub.challenge", "")
    if mode == "subscribe" and token == _VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Forbidden")


@app.post("/webhook/whatsapp")
async def whatsapp_inbound(request: Request) -> dict[str, bool]:
    """Receive inbound WhatsApp messages and resolve pending approval futures."""
    try:
        body = await request.json()
        msg = body["entry"][0]["changes"][0]["value"]["messages"][0]
        text = msg.get("text", {}).get("body", "").strip().lower()
    except (KeyError, IndexError, Exception):
        return {"ok": True}

    if APPROVALS_WAITING:
        run_id = next(reversed(APPROVALS_WAITING))
        if text in {"approve", "yes", "y", "ok"}:
            resolve_approval(run_id, "approved")
        elif text in {"reject", "no", "n", "skip"}:
            resolve_approval(run_id, "rejected")

    return {"ok": True}

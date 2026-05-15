"""Smoke test for LangGraph orchestrator + SQLite checkpoints (BUILD.md Task 1.1)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from agents.orchestrator.graph import build_graph
from agents.orchestrator.state import AppState


def _initial_state(run_id: str = "run-smoke-1") -> AppState:
    return {
        "run_id": run_id,
        "jd_id": "JD-001",
        "jd_url": "https://boards.greenhouse.io/example/jobs/123",
        "jd_text": "Senior ML Engineer — Python, PyTorch.",
        "track": None,
        "score": None,
        "report_path": None,
        "pdf_path": None,
        "cover_path": None,
        "ats_family": None,
        "autonomy_level": 1,
        "errors": [],
        "gate_pending": None,
        "screenshot_path": None,
    }


def test_graph_runs_and_writes_checkpoint(tmp_path: Path) -> None:
    db_path = tmp_path / "checkpoints.sqlite"
    with SqliteSaver.from_conn_string(str(db_path)) as saver:
        graph = build_graph(saver)
        cfg = {"configurable": {"thread_id": "thread-smoke-1"}}
        out = graph.invoke(_initial_state(), cfg)

    assert out.get("score") == 4.2
    assert out.get("track") == "MLE"
    assert out.get("ats_family") == "greenhouse"

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT COUNT(*) FROM checkpoints").fetchone()
    conn.close()
    assert row is not None and row[0] >= 1

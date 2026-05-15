"""LangGraph orchestrator skeleton with SQLite checkpoints (BUILD.md Task 1.1)."""

from __future__ import annotations

from typing import Literal

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from agents.orchestrator.state import AppState


def _stub_score_jd(jd_text: str) -> dict[str, object]:
    """Placeholder until ``agents.workers.scorer`` (Task 1.2)."""
    _ = jd_text
    return {"track": "MLE", "score": 4.2, "report_path": "reports/stub-report.md"}


def _stub_tailor(jd_text: str, track: str | None, run_id: str) -> dict[str, str]:
    _ = jd_text, track
    return {
        "pdf_path": f"output/{run_id}.pdf",
        "cover_path": f"output/{run_id}-cover.md",
    }


def _stub_drive(
    jd_url: str, pdf_path: str | None, cover_path: str | None, run_id: str
) -> dict[str, str]:
    _ = jd_url, pdf_path, cover_path, run_id
    return {"ats_family": "greenhouse"}


def _stub_verify(run_id: str, jd_url: str) -> dict[str, bool]:
    _ = run_id, jd_url
    return {"confirmed": True}


def n_score(state: AppState) -> dict[str, object]:
    res = _stub_score_jd(state["jd_text"])
    return {"track": res["track"], "score": res["score"], "report_path": res["report_path"]}


def r_after_score(state: AppState) -> Literal["tailor", "end"]:
    sc = state.get("score")
    if sc is None or sc < 4.0:
        return "end"
    return "tailor"


def n_tailor(state: AppState) -> dict[str, str | None]:
    out = _stub_tailor(state["jd_text"], state.get("track"), state["run_id"])
    return {"pdf_path": out["pdf_path"], "cover_path": out["cover_path"]}


def n_pdf_gate(state: AppState) -> dict[str, object]:
    """HITL PDF gate placeholder (WhatsApp / bridge approval wired in later tasks)."""
    _ = state
    return {}


def n_apply(state: AppState) -> dict[str, str | None]:
    res = _stub_drive(
        state["jd_url"],
        state.get("pdf_path"),
        state.get("cover_path"),
        state["run_id"],
    )
    return {"ats_family": res["ats_family"]}


def n_verify(state: AppState) -> dict[str, object]:
    res = _stub_verify(state["run_id"], state["jd_url"])
    if res["confirmed"]:
        return {}
    return {"errors": ["unverified_submission"]}


def build_graph(checkpointer: SqliteSaver):
    """Compile graph with the given SQLite checkpointer (caller manages lifetime)."""
    g = StateGraph(AppState)
    g.add_node("score", n_score)
    g.add_node("tailor", n_tailor)
    g.add_node("pdf_gate", n_pdf_gate)
    g.add_node("apply", n_apply)
    g.add_node("verify", n_verify)
    g.add_edge(START, "score")
    g.add_conditional_edges("score", r_after_score, {"tailor": "tailor", "end": END})
    g.add_edge("tailor", "pdf_gate")
    g.add_edge("pdf_gate", "apply")
    g.add_edge("apply", "verify")
    g.add_edge("verify", END)
    return g.compile(checkpointer=checkpointer)

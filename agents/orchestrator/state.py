"""Orchestrator state schema (BUILD.md Task 1.1, arch.G.3)."""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class AppState(TypedDict):
    """LangGraph channel state for the apply pipeline."""

    run_id: str
    jd_id: str
    jd_url: str
    jd_text: str
    track: str | None
    score: float | None
    report_path: str | None
    pdf_path: str | None
    cover_path: str | None
    ats_family: str | None
    autonomy_level: int
    errors: Annotated[list[str], operator.add]
    gate_pending: str | None
    screenshot_path: str | None

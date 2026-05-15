"""
HTTP control plane for the LangGraph stack (BUILD.md Task 0.6+).

Runs on localhost only by default — never expose raw to the public internet without TLS and auth.
"""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="Career Ops Bridge",
    version="0.1.0",
    description="Local HITL + status API for the autonomous applier (see BUILD.md).",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe for launchd / CI / dashboard integrations."""
    return {"status": "ok"}

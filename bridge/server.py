"""
HTTP control plane for the LangGraph stack (BUILD.md Task 0.6+).

Runs on localhost only by default — never expose raw to the public internet without TLS and auth.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from fastapi import FastAPI

_REPO_ROOT = Path(__file__).resolve().parents[1]


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
)


@app.get("/health")
def health() -> dict[str, bool | str]:
    """Liveness: ``ok`` + ``version`` (git short SHA when available). BUILD.md Task 0.6."""
    return {"ok": True, "version": _git_short_sha()}

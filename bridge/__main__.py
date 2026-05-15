"""Run with: ``uv run python -m bridge`` (serves ``GET /health`` on loopback only)."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    raw_host = os.environ.get("CAREEROPS_BRIDGE_HOST", "127.0.0.1")
    if raw_host in {"0.0.0.0", "::"}:
        raise SystemExit(
            "CAREEROPS_BRIDGE_HOST must be loopback (127.0.0.1 or ::1). "
            "Binding all interfaces is not allowed for the bridge (BUILD.md Task 0.6)."
        )
    port = int(os.environ.get("CAREEROPS_BRIDGE_PORT", "8765"))
    uvicorn.run("bridge.server:app", host=raw_host, port=port, factory=False)


if __name__ == "__main__":
    main()

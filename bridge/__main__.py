"""Run with: ``uv run python -m bridge`` (serves ``GET /health``)."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.environ.get("CAREEROPS_BRIDGE_HOST", "127.0.0.1")
    port = int(os.environ.get("CAREEROPS_BRIDGE_PORT", "8765"))
    uvicorn.run("bridge.server:app", host=host, port=port, factory=False)


if __name__ == "__main__":
    main()

# Career-ops-autonomus

Autonomous job-application stack (Python orchestrator + local bridge) per **`BUILD.md`** and the in-repo architecture artifact.

## Quick start (Python)

- Install [**uv**](https://docs.astral.sh/uv/).
- `uv sync --all-groups`
- `uv run pytest -q`
- `uv run python -m bridge` then open `http://127.0.0.1:8765/health`

## Nix / direnv

`flake.nix` pins the dev shell (Python 3.12, uv, Node 20, Go 1.22). Run `nix flake lock` on a machine with Nix, then commit `flake.lock` when ready.

## Agent rules

Read **`BUILD.md`** first. Contracts: **`AGENTS.md`**, **`CLAUDE.md`**, **`DATA_CONTRACT.md`**, **`LEGAL_DISCLAIMER.md`**.

Upstream evaluation tooling from **`santifer/career-ops`** is planned to be vendored or linked later; `npm run doctor` currently validates scaffold layout.

# Claude Code instructions

> **Build progress lives in `BUILD.md`.** Read it at session start and follow its Update Protocol.

## First action each session

1. Read **`BUILD.md`** top to bottom — it is the single source of truth for task order, verify commands, and hard rules.
2. Read **`AGENTS.md`**, **`DATA_CONTRACT.md`**, and **`LEGAL_DISCLAIMER.md`** before changing behavior that touches user data or browsers.
3. Work the **next unchecked** `BUILD.md` task whose dependencies are satisfied; do not skip phases.

## Autonomous Mode (applier / LangGraph)

Any agent or worker that can drive browsers or call ATS APIs **must** route risky actions through `request_human_approval(...)` (or equivalent LangGraph `interrupt()` gates) until **`autonomy_level`** in runtime state meets the threshold configured in `config/profile.yml` for that gate. Never bypass final-submit approval by configuration alone without an explicit user decision recorded in the `approvals` table / audit trail.

The numeric **autonomy_level** (0–4) is documented in **`docs/AUTONOMY.md`**. Default posture for development remains **level 1** (approve everything material).

## Progress bookkeeping

When you complete a task, update **`BUILD.md`** checkboxes and the **📍 Current Status** block in the **same commit** as the code (see Update Protocol in `BUILD.md`).

## Where architecture detail lives

Cross-reference the markdown artifact in-repo: `compass_artifact_wf-08594742-2800-4888-a3c1-512b10deab8d_text_markdown.md` (sections cited as `arch.A`, `arch.B`, … in `BUILD.md`).

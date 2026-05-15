# Claude Code instructions

## First action each session

1. Read **`BUILD.md`** top to bottom — it is the single source of truth for task order, verify commands, and hard rules.
2. Read **`AGENTS.md`**, **`DATA_CONTRACT.md`**, and **`LEGAL_DISCLAIMER.md`** before changing behavior that touches user data or browsers.
3. Work the **next unchecked** `BUILD.md` task whose dependencies are satisfied; do not skip phases.

## Progress bookkeeping

When you complete a task, update **`BUILD.md`** checkboxes and the **📍 Current Status** block in the **same commit** as the code (see Update Protocol in `BUILD.md`).

## Where architecture detail lives

Cross-reference the markdown artifact in-repo: `compass_artifact_wf-08594742-2800-4888-a3c1-512b10deab8d_text_markdown.md` (sections cited as `arch.A`, `arch.B`, … in `BUILD.md`).

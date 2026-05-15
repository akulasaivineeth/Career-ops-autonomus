# Agent contract

## Purpose

This repository implements an **autonomous job-application operating system** alongside user-owned markdown artifacts. Agents (Claude Code, Cursor, or future LangGraph workers) must preserve human control and legal guardrails.

## Non-negotiables

1. **No final submit** on a live job site without explicit human approval through the designed HITL channel (`request_human_approval("final_submit", …)` in code).
2. **No LinkedIn profile scraping** — Easy Apply flows only, per architecture doc §A.
3. **No plaintext secrets** in the repo, logs, or agent transcripts — use Keychain / `agents.tools.keychain` only.
4. **`data/applications.md` and related markdown** remain user-owned; never bulk-overwrite without an approved migration tool (see `DATA_CONTRACT.md`).
5. **Build progress** is tracked in **`BUILD.md`** — read the Update Protocol at session start.

## Skills and modes

Canonical prompts live under `modes/` (to be populated from upstream `santifer/career-ops` or rewritten here). Python orchestration lives under `agents/` and `bridge/`.

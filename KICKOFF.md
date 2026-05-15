# KICKOFF — Paste this into your first Claude Code / Cursor session

> **Step 1:** Save `BUILD.md` and this `KICKOFF.md` to the repo root.
> **Step 2:** Commit them: `git add BUILD.md KICKOFF.md && git commit -m "chore: add build plan + kickoff"`.
> **Step 3:** Open Claude Code (`claude` in repo root) or Cursor (Cmd+L). Paste the block below as your first message.

---

## The kickoff prompt to paste

```
You are working on `santifer/career-ops`, extending it into an autonomous
multi-agent Job Application OS for macOS Apple Silicon. The plan is
already written. Your job is to execute it task-by-task with maximum
care, maximum human-in-the-loop, and zero shortcuts.

PHASE 1 of this conversation (before any code):

1. Read BUILD.md in full. The file is at the repo root. It contains:
   - "Tech Stack" table — languages, versions, package managers, locations.
   - "Folder layout" — exact directory tree you will build out.
   - "Secret-Prompt Protocol" — how to ask me for API keys without ever
     seeing or storing them in plaintext.
   - "Update Protocol" — how you mark tasks done and commit progress.
   - "Hard rules" — twelve things you must never do.
   - 48 numbered tasks across Phase −1 (cold start), Phase 0
     (foundations), Phase 1 (MVP applier), Phase 2 (multi-site), Phase 3
     (volume), Phase 4 (autonomy), Phase 5 (hardening).

2. Read CLAUDE.md, AGENTS.md, DATA_CONTRACT.md, LEGAL_DISCLAIMER.md so
   you understand existing repo conventions you must preserve.

3. Confirm to me, in your reply, by stating:
   - The current "Now" task ID and title from BUILD.md.
   - Its dependencies and whether they are satisfied.
   - The acceptance criteria and verify command.
   - Any ambiguity you need clarified BEFORE writing or running anything.

PHASE 2 of this conversation (per-task loop, forever):

For every task you work, follow this exact loop:

a. Post a session TODO list (use the TodoWrite tool if you have it, or
   a numbered list otherwise) showing the sub-steps for the current
   BUILD.md task only — NOT the whole phase.

b. Post a one-paragraph "plan to start" summary: files I'll touch, tests
   I'll write, verify command, estimated diff size. Then WAIT for me to
   reply "go" before any file creation or shell command.

c. If the task needs a secret, post the Secret-Prompt Protocol message
   exactly as specified in BUILD.md. WAIT for me to confirm "stored"
   before proceeding. NEVER assume, hardcode, or use placeholder secrets.

d. Implement only the files listed under the task's "Files:" field.
   Run the "Verify:" command at the end and paste its output to me.

e. When verify passes:
   - Flip the BUILD.md checkbox from `- [ ]` to
     `- [x] ✅ YYYY-MM-DD <commit-sha-short>`.
   - Update the "📍 Current Status" block at the top of BUILD.md.
   - Stage BUILD.md alongside the code changes.
   - Show me `git diff --stat` and the proposed commit message.
   - WAIT for me to reply "approve commit" before `git commit`.

f. If you hit a blocker:
   - Append a row to BUILD.md's "🚧 Blockers" table.
   - Leave the task `- [ ]`. Do NOT mark partial completion.
   - Surface the blocker to me and STOP.

g. If you choose a different library/structure/approach than BUILD.md
   specifies:
   - Append a row to BUILD.md's "🧱 Decision Log".
   - Surface the choice to me and ASK before proceeding.

HARD RULES (BUILD.md §"Hard rules" — repeated here for emphasis):

- NEVER click a final-submit button on a live job site during build.
- NEVER store API keys or passwords in plaintext. Use Keychain only.
- NEVER commit `audit/`, `output/`, `db/careerops.db*`, browser context
  dirs, `.env`, OAuth client secrets.
- NEVER scrape LinkedIn profiles. Easy Apply only.
- NEVER mark a task complete you did not personally implement and
  verify this session.
- NEVER skip a task or work tasks out of dependency order.
- NEVER run `git push` without my explicit say-so.
- NEVER use `sudo`, `rm -rf`, `git reset --hard`, or any destructive
  command without my confirmation.
- NEVER install global npm/pip packages — everything project-local.
- NEVER answer "yes" to a prompt on my behalf (OAuth consent, Keychain
  access dialog, CAPTCHA challenge, etc).
- If anything is unclear: append a Blocker row to BUILD.md and STOP.
  Do not guess.

Architecture decisions and full agent prompts live in the conversation
artifact "Autonomous Multi-Agent Job Application OS: Architecture
Blueprint for macOS Apple Silicon". Each BUILD.md task has a "Refs:"
field pointing to the relevant section (arch.A, arch.B.4, arch.G.3, etc).

Begin Phase 1 now: read BUILD.md and the four existing repo contract
files, then report back per step 3 above. Do not execute Task −1.1 yet.
```

---

## How the auto-tracking actually works

Three mechanisms, all wired into `BUILD.md`:

1. **Checkbox flip.** Every task is a single line `- [ ]`. When the agent finishes a task, it edits that line to `- [x] ✅ 2026-05-15 abc1234` (date + short commit SHA). Trivially reliable — it's just a string replacement.

2. **Status header.** The "📍 Current Status" block at the top is the at-a-glance view. The agent rewrites it on every task completion: bumps "Completed tasks" count, sets "Active task" back to None, and rolls the "Now / Next / Later" pointers forward.

3. **Single commit ties code + plan.** Because `BUILD.md` is committed in the same commit as the code change (`feat(0.4): keychain wrapper` includes the BUILD.md flip), every git log entry is a verifiable audit of "task N.N was completed in commit X."

If you ever want to see overall progress without opening a file:

```bash
echo "$(grep -c '^- \[x\]' BUILD.md) / $(grep -c '^- \[' BUILD.md) tasks complete"
```

---

## What changed vs. a naive plan

The plan you're handing the agent has **five built-in safeguards** that a typical "build me X" prompt lacks:

1. **Phase −1 cold start.** Eight tasks BEFORE any code, covering: clone the repo, create a branch, verify Nix/Node/Go, confirm Apple Silicon + RAM, prompt for the Anthropic API key, place the Gmail OAuth client secret, verify Keychain round-trip. This means the agent can't fail with "I don't have credentials" three tasks in.

2. **Secret-Prompt Protocol.** The agent posts a fixed-format message asking you for each secret. You run a one-liner in *your own* terminal that pipes the secret into macOS Keychain without echo. The agent never sees the value, never logs it, never commits it, never uses `"REPLACE_ME"` placeholders.

3. **Session TODO + BUILD.md TODO.** Two layers — the session todo shows you the sub-steps of the current task in real time (Claude Code's `TodoWrite` panel); BUILD.md tracks the high-level 48-task plan. They complement each other.

4. **"Go" gates everywhere.** Before any task, before any commit, before any secret request → the agent stops and waits for your explicit OK. You're never surprised by what runs.

5. **Decision log + blocker table.** Anything that deviates from the plan, or anything that gets stuck, is recorded in BUILD.md itself. After a few weeks of work, you can read the file top to bottom and reconstruct exactly what happened and why.

---

## Running this with Claude Code specifically

- **Claude Code has a built-in `TodoWrite` tool** for in-session sub-task tracking. The agent will use it for the sub-steps inside a single BUILD.md task. The session-scoped todos are **complementary** to BUILD.md, not a replacement.
- **Claude Code reads `CLAUDE.md` automatically on every session.** Task 0.8 adds a single line to `CLAUDE.md`: *"Build progress lives in `BUILD.md`. Read it at session start and follow its Update Protocol."* After Task 0.8 ships, you won't need to re-paste this kickoff in future sessions — Claude Code will pick up the contract from `CLAUDE.md` automatically.
- **For Cursor:** add a `.cursor/rules/career-ops.mdc` file with the same pointer + the hard rules. Cursor will inject it into every chat. (Suggest the agent do this in Task 0.8 as well.)
- **Commit hygiene:** the agent uses `git commit -m "feat(N.N): <title>"` so `git log --oneline` becomes a readable build journal.

---

## When you want to check progress between sessions

Open `BUILD.md`. The top block shows you exactly where you are. Scroll to find the first `- [ ]` after a string of `- [x]`s — that's the next task. The "🚧 Blockers" section shows anything stuck. The "🧱 Decision Log" shows where the agent deviated from the original plan and why.

For a one-glance terminal view: `glow BUILD.md` (markdown CLI viewer) or just `head -40 BUILD.md`.

---

## Recommended first 30 minutes

1. `git clone git@github.com:santifer/career-ops.git ~/code/career-ops`
2. `cd ~/code/career-ops` and save `BUILD.md` + `KICKOFF.md` to the repo root.
3. `git add BUILD.md KICKOFF.md && git commit -m "chore: add build plan + kickoff"`
4. `claude` (or open Cursor and Cmd+L).
5. Paste the kickoff prompt block above as your first message.
6. The agent will read BUILD.md and report back. Confirm Task −1.1 is up next, give "go", and you're building.

Human supervision required throughout. There is no "set it and forget it" — by design.

# career-ops — Autonomous Job Application OS Build Plan

> **Single source of truth for build progress.** Claude Code, Cursor, or any agent working on this repo must read this file fully at session start, work the next unblocked task, mark it complete, and commit this file with the code in the same commit.

---

## 📍 Current Status

| Field | Value |
|---|---|
| **Phase** | Phase 1 — MVP applier (skeleton landed; Nix Task 0.1 still open) |
| **Last updated** | 2026-05-15 |
| **Active task** | None |
| **Completed tasks** | 8 / 48 (through Task 1.1 skeleton on this fork; see Decision Log) |
| **Blockers** | None |
| **Autonomy level** | 0 (build mode; no live applies yet) |
| **Repo cloned?** | ✅ `Career-ops-autonomus` (fork scaffold; upstream `santifer/career-ops` optional) |
| **Toolchain ready?** | ⚠️ `uv` + Python 3.12 in CI; full `nix develop` + `flake.lock` pending Task 0.1 |
| **Secrets configured?** | ❌ Not yet — run Tasks −1.5 through −1.7 on your Mac |

### 🎯 Now / Next / Later

- **Now:** Task 1.2 (scorer worker) or Task 0.1 (Nix + `flake.lock`)
- **Next:** Tailor worker (1.3), adapters (1.4+)
- **Later:** Phase 1 MVP apply path

---

## 🛠 Tech Stack — Languages, Versions, Locations (read this once, then memorize)

This project mixes **three languages** by design. The existing repo is Node.js + Go; we are grafting on a Python sub-system without rewriting anything.

| Layer | Language | Version | Package manager | Location | Purpose |
|---|---|---|---|---|---|
| **Existing Claude Code skills** | Markdown | — | — | `modes/*.md`, `.agents/skills/`, `.claude/skills/` | User-facing agent prompts |
| **Existing scan/PDF/verify scripts** | Node.js (ESM) | 20.x LTS | `npm` | `*.mjs` at repo root | Existing scanners, PDF generation, dedup, doctor |
| **Existing dashboard TUI** | Go | 1.22+ | `go mod` | `dashboard/` | Bubble Tea + Lipgloss TUI |
| **NEW orchestrator + workers + tools + adapters** | Python | 3.12 (exact) | `uv` (`uv.lock` committed) | `agents/`, `bridge/` | LangGraph state machine, Playwright applier, Gmail/WhatsApp/Keychain tools |
| **NEW database** | SQLite (SQLCipher in Phase 5) | 3.45+ | — | `db/careerops.db` | LangGraph checkpoints, audit log, embeddings |
| **Reproducibility** | Nix flake | flakes enabled | `nix` | `flake.nix`, `flake.lock` | Pins everything above |

**Do NOT** introduce new languages (no Rust, no Ruby, no Bun). **Do NOT** swap Python for TypeScript-Node "because LangChain.js exists" — LangGraph's Python implementation has the HITL `interrupt()` + `SqliteSaver` semantics this project specifically depends on. **Do NOT** use `pip`, `pipenv`, or `poetry` — `uv` only. **Do NOT** use `conda`/`mamba` — `uv` only. If a dependency only exists in TypeScript, wrap it in a thin Node `.mjs` script and call it via `subprocess` from Python (the pattern is already established with the existing `generate-pdf.mjs`).

**Folder layout — final state at end of Phase 5:**

```
career-ops/
├── AGENTS.md                    # existing — agent contract (DO NOT REWRITE)
├── BUILD.md                     # this file — build plan + progress
├── CLAUDE.md                    # existing — Claude Code instructions (EXTEND, don't rewrite)
├── DATA_CONTRACT.md             # existing — markdown files are user-owned (HONOR)
├── KICKOFF.md                   # one-time bootstrap prompt
├── LEGAL_DISCLAIMER.md          # existing (EXTEND with autonomous-mode warnings)
├── README.md                    # existing
├── flake.nix / flake.lock       # extended in Task 0.1
├── pyproject.toml / uv.lock     # NEW — Python deps via uv (Task 0.3)
├── package.json                 # existing — Node deps
├── go.mod / go.sum              # existing — Go deps (dashboard)
├── .envrc                       # existing — direnv
├── .gitignore                   # extended in Task 0.2
│
├── modes/                       # existing — Claude Code modes (apply.md rewritten in 1.8)
├── batch/                       # existing — shell batch runner
├── config/                      # existing — profile.yml, portals.yml
├── templates/                   # existing — cv-template.html, states.yml
├── fonts/                       # existing
├── data/                        # existing — applications.md, pipeline.md, scan-history.tsv
├── reports/                     # existing — eval markdown
├── output/                      # existing — generated PDFs (GITIGNORED)
├── jds/                         # existing — JD text dumps
├── dashboard/                   # existing — Go TUI
│
├── agents/                      # NEW
│   ├── orchestrator/            # LangGraph StateGraph
│   │   ├── graph.py             # Task 1.1
│   │   ├── state.py             # Task 1.1
│   │   ├── autonomy.py          # Task 4.1
│   │   └── auto_pass.py         # Task 4.2
│   ├── workers/                 # one .py per agent role
│   │   ├── scanner.py           # Task 3.1
│   │   ├── scorer.py            # Task 1.2
│   │   ├── tailor.py            # Task 1.3
│   │   ├── applier.py           # Task 1.6
│   │   ├── verifier.py          # Task 3.2
│   │   ├── anomaly.py           # Task 4.3
│   │   └── digest.py            # Task 4.4
│   ├── adapters/                # per-site ATS drivers
│   │   ├── base.py              # Task 1.4
│   │   ├── ats_greenhouse.py    # Task 1.4
│   │   ├── ats_lever.py         # Task 2.1
│   │   ├── ats_ashby.py         # Task 2.2
│   │   ├── ats_workday.py       # Task 2.3
│   │   ├── ats_indeed.py        # Task 2.4
│   │   ├── ats_glassdoor.py     # Task 2.4
│   │   ├── ats_wellfound.py     # Task 2.5
│   │   ├── ats_linkedin.py      # Task 2.6
│   │   └── ats_generic.py       # Task 2.7
│   ├── tools/                   # shared utilities
│   │   ├── keychain.py          # Task 0.4
│   │   ├── gmail.py             # Task 0.5
│   │   ├── whatsapp.py          # Task 1.5
│   │   ├── browser_harness.py   # Task 1.6
│   │   ├── computer_use.py      # Task 1.6
│   │   ├── captcha.py           # Task 2.8
│   │   ├── embeddings.py        # Task 3.3
│   │   ├── rate_limiter.py      # Task 3.6
│   │   ├── circuit.py           # Task 5.3
│   │   ├── redact.py            # Task 5.2
│   │   ├── session_health.py    # Task 5.4
│   │   ├── llm_local.py         # Task 3.2 (Ollama shim)
│   │   └── db.py                # Task 5.1 (SQLCipher wrapper)
│   ├── prompts/                 # canonical system prompts (one .md each)
│   └── tests/                   # pytest suite (test_*.py)
│
├── bridge/                      # NEW — local FastAPI control plane
│   ├── server.py                # Task 0.6 scaffold, extended in 1.7
│   ├── __main__.py              # Task 0.6
│   └── approvals.py             # Task 1.7
│
├── db/                          # NEW
│   ├── careerops.db             # GITIGNORED runtime DB
│   ├── schema.sql               # Task 0.7
│   ├── migrate.py               # Task 0.7
│   └── migrations/
│       ├── 0001_init.sql
│       └── 0002_jd_embeddings_index.sql
│
├── audit/                       # NEW — per-run screenshots, DOM diffs (GITIGNORED)
│
├── cv/                          # NEW — three resume tracks (USER edits these)
│   ├── README.md                # Task 3.4
│   ├── da.md                    # Task 3.4
│   ├── mle.md                   # Task 3.4
│   └── de.md                    # Task 3.4
│
├── infra/                       # NEW — launchd plists + install scripts
│   ├── com.career-ops.daily.plist        # Task 3.5
│   ├── com.career-ops.weekly.plist       # Task 4.4
│   ├── com.career-ops.healthcheck.plist  # Task 5.4
│   └── install-launchd.sh                # Task 3.5
│
├── scripts/                     # NEW — one-off ops scripts
│   ├── migrate-applications-md.mjs       # Task 1.9
│   └── save-linkedin-session.mjs         # Task 2.6
│
├── bin/                         # NEW — user-facing CLIs
│   ├── career-apply             # Task 1.8
│   └── career-ops-daily         # Task 3.5
│
└── docs/                        # NEW — user-facing docs
    ├── AUTONOMY.md              # Task 0.8
    ├── SECRETS.md               # Task 0.4
    ├── GMAIL_SETUP.md           # Task 0.5
    ├── WHATSAPP_SETUP.md        # Task 1.5
    ├── LINKEDIN_SESSION.md      # Task 2.6
    ├── CV_TRACKS.md             # Task 3.4
    ├── SCHEDULING.md            # Task 3.5
    └── ENCRYPTION.md            # Task 5.1
```

---

## 🔐 Secret-Prompt Protocol — read before working

The agent will need API keys, OAuth tokens, and passwords. **It must NEVER assume them, hardcode them, or fabricate them.** When a task requires a secret, the agent follows this exact sequence:

1. **Check Keychain first** via `agents.tools.keychain.get_secret(name)` (or `security find-generic-password` in cold-start phase). If present, use it.
2. **If absent**, the agent STOPS and posts to the user a message in this exact format:

   ```
   🔐 I need a secret to continue Task <N.N>: <task title>.

   Secret name (Keychain service): careerops.<name>
   Account:                         <account or "default">
   What it is:                      <one-line description>
   Where to get it:                 <URL + 1-2 step instructions>
   Required scope/permissions:      <minimum scopes>

   In YOUR terminal (NOT mine), run exactly:
     read -s VAL && security add-generic-password -U \
       -s careerops.<name> -a <account> -w "$VAL" && unset VAL && echo stored

   Paste the value into the hidden prompt. I will NOT see it. I will NOT
   echo it, NOT commit it, NOT log it. Reply "stored" when you see "stored"
   and I'll continue Task <N.N>.
   ```

3. **The agent waits.** No code runs that depends on the secret until the user replies "stored" and the agent confirms with `security find-generic-password -s careerops.<name> -a <account> -w >/dev/null && echo OK` (this only prints OK, never the value).
4. **The agent NEVER:**
   - Asks for secrets in the same message it is asking other questions (one prompt = one secret).
   - Echoes the value back in any subsequent message, log line, or commit.
   - Writes the value to a file under any circumstance.
   - Stores it in `.env`, `config/*.yml`, or any tracked file.
   - Uses `print()` or `console.log` on the value.
   - Continues with a placeholder like `"REPLACE_ME"` — that is a blocker, not a workaround.
5. **Secrets the agent will ask for** (in this order, as the build progresses):

   | Task | Service name | Account | What | Where to get |
   |---|---|---|---|---|
   | −1.5 | `careerops.anthropic` | `api_key` | Anthropic Claude API key | console.anthropic.com → API Keys |
   | 0.5 | `careerops.gmail` | `oauth_token_json` | Gmail OAuth refresh token | Set automatically by `make oauth-gmail` after user places `client_secret.json` (Task −1.6) |
   | 1.5 | `careerops.whatsapp` | `access_token` | WhatsApp Cloud API permanent token | developers.facebook.com → app → WhatsApp → API Setup → System users → permanent token |
   | 1.5 | `careerops.whatsapp` | `webhook_verify_token` | Webhook verify token (you invent this, 32+ chars) | `openssl rand -hex 32` |
   | 2.8 | `careerops.capsolver` | `api_key` | CapSolver API key | dashboard.capsolver.com → API |
   | 2.8 | `careerops.twocaptcha` | `api_key` | 2Captcha API key (fallback) | 2captcha.com → API |
   | 5.1 | `careerops.db` | `encryption_key` | SQLCipher passphrase | `openssl rand -hex 32` |

6. **Environment variables the agent will ask you to set** (non-secret, may go in `.envrc`):

   | Task | Variable | Example | Purpose |
   |---|---|---|---|
   | 0.8 | `CAREEROPS_VAULT` | `keychain` | Vault backend (`keychain` / `op` / `bw`) |
   | 1.5 | `WA_PHONE_NUMBER_ID` | `109361185504724` | Meta-assigned WhatsApp business phone ID |
   | 1.5 | `WA_USER_NUMBER` | `+15551234567` | Your personal WhatsApp number with country code |

---

## 🔄 Update Protocol — read before working

Every agent session on this repo must follow this loop:

1. **Read this file fully.** Note the current phase and the "Now" task.
2. **Maintain a session TODO.** At session start, after reading BUILD.md, the agent posts a session-scoped TODO list to the user (Claude Code: use the `TodoWrite` tool; Cursor: use its native todo panel; if neither: post a numbered list in the chat). This TODO mirrors the sub-steps of the CURRENT BUILD.md task, NOT the whole phase. Format:
   ```
   Session TODO for Task <N.N> — <title>:
     [ ] sub-step 1 — read existing files X, Y
     [ ] sub-step 2 — write file A
     [ ] sub-step 3 — write tests
     [ ] sub-step 4 — run verify command
     [ ] sub-step 5 — flip checkbox + update status block
     [ ] sub-step 6 — show diff and propose commit message
   ```
   The agent updates this TODO live (check items off as they complete) so the user can see at any time exactly what is next.
3. **Pick the next BUILD.md task** with `- [ ]` whose `Depends on:` items are all `- [x]`. Within a phase, prefer the lowest-numbered such task. Do not skip phases.
4. **Read the task block end-to-end** before writing any code. Cross-reference the architecture doc section listed under `Refs:`.
5. **Confirm with the user before starting.** Post a one-paragraph summary: "I'll work Task N.N. Files I'll touch: …. Tests I'll write: …. Verify command: …. Estimated changes: ~X lines across Y files. Reply 'go' to proceed." **WAIT for explicit "go"** before any file creation.
6. **Implement.** Touch only the files listed under `Files:` plus anything strictly necessary (note additions in the commit message).
7. **Prompt for any secret** per the Secret-Prompt Protocol above. Never guess, never use placeholders.
8. **Run the verify command** under `Verify:`. Paste its output to the user. If it fails, debug. Do not mark the task complete until verify passes cleanly.
9. **Mark complete:**
   - Flip `- [ ]` → `- [x] ✅ YYYY-MM-DD <commit-sha-short>` on the task line.
   - Update the **📍 Current Status** block at the top (Phase, Last updated, Active task → None, Completed tasks +1, Now/Next/Later pointers).
   - If you added sub-tasks during work, list them as `  - [x]` indented bullets under the parent task.
   - **Commit `BUILD.md` together with the code change** in a single commit. Suggested message: `feat(N.N): <task title>` for new functionality, `chore(plan): complete N.N` for plan-only edits.
   - Show the user `git diff --stat` and the proposed commit message. **WAIT for "approve commit"** before `git commit`.
10. **On blockers:**
    - Append a dated entry to **🚧 Blockers** with: task ID, what failed, error message, what you tried, what's needed to unblock.
    - Leave the task `- [ ]`. Do NOT mark partial completion.
    - Surface the blocker in your final message to the user and STOP.
11. **On architectural deviations:**
    - If you choose a different library, structure, or approach than the architecture doc, append to **🧱 Decision Log** with date, decision, rationale, diff link. Surface to user and ask for confirmation BEFORE committing.
12. **Hard rules — never violated:**
    - NEVER mark a task complete you did not personally implement and verify this session.
    - NEVER delete or rewrite completed task entries — they are an audit trail.
    - NEVER click a final-submit button on any live job site during build. The applier code path must always go through `request_human_approval("final_submit", ...)`. There is no skip flag.
    - NEVER store secrets in plaintext. Always go through `agents.tools.keychain`.
    - NEVER run `git push` without explicit user say-so.
    - NEVER run `rm -rf`, `git reset --hard`, `git clean -fd`, or any destructive command without user confirmation.
    - NEVER commit `output/`, `audit/`, `*.pdf`, browser context dirs, `db/careerops.db*`, `.env`, OAuth client secrets, or anything matching the .gitignore patterns set in Task 0.2.
    - NEVER use `sudo` without asking.
    - NEVER install global npm/pip packages — everything is project-local via `uv` or `npm install --save-dev`.
    - NEVER answer "yes" to a prompt on the user's behalf without explicit instruction (CAPTCHA, OAuth consent, Keychain access dialogs, `launchctl bootout`, etc.).

---

## 📚 Reference Documents

- **Architecture doc:** see Claude conversation artifact "Autonomous Multi-Agent Job Application OS: Architecture Blueprint for macOS Apple Silicon" (sections A–G referenced below as `arch.A`, `arch.B.4`, etc.)
- **Existing repo contracts:** `AGENTS.md`, `CLAUDE.md`, `DATA_CONTRACT.md`, `LEGAL_DISCLAIMER.md`, `modes/_shared.md`
- **Profile:** `config/profile.yml` (extended in Phase 0)

---

## 📋 Phase −1 — Cold Start (BEFORE any code is written)

**Phase goal:** Get the agent and the local machine into a known-good state. Repo cloned, branch created, all toolchains verified, secrets prompted for and stored, NO code changes yet.

**Phase exit criteria:** Agent can run `git status`, `nix develop --command bash -c "python --version && uv --version && node --version && go version && ollama --version"` and all succeed. Branch `feat/autonomous-applier` is checked out. All Phase 0 prerequisite secrets are stored in Keychain.

---

### - [ ] Task −1.1 — Clone repo and create build branch
- **Files:** none yet (working-directory setup)
- **Depends on:** —
- **Acceptance:**
  - User has cloned `git@github.com:santifer/career-ops.git` (or `https://github.com/santifer/career-ops.git` if no SSH) to `~/code/career-ops` (agent suggests this path; user may override).
  - `git remote -v` shows `origin` pointing at `santifer/career-ops`.
  - Working tree is on a NEW branch `feat/autonomous-applier` cut from `main`.
  - `git status` shows clean working tree (no uncommitted changes).
  - `BUILD.md` and `KICKOFF.md` are present at repo root (user placed them).
- **Agent prompt to user (post BEFORE running anything):**
  ```
  Before I touch anything, please confirm:

  1. Have you cloned the repo locally? If yes, what is the absolute path?
     (Suggested: ~/code/career-ops)
  2. Are BUILD.md and KICKOFF.md placed at the repo root?
  3. Are you OK with me creating a branch `feat/autonomous-applier`
     from `main` for the entire build?

  Reply with the path + yes/no. I will run `git fetch + status` and
  show you the output before creating the branch.
  ```
- **Agent commands (run one at a time, show output to user):**
  ```bash
  pwd
  git rev-parse --show-toplevel              # confirm we are in the repo
  git remote -v
  git status
  git fetch origin
  git checkout main && git pull --ff-only
  git checkout -b feat/autonomous-applier
  ls BUILD.md KICKOFF.md                     # confirm both present
  ```
- **Verify:**
  ```bash
  git rev-parse --abbrev-ref HEAD            # → feat/autonomous-applier
  git status --porcelain                     # → empty
  test -f BUILD.md && test -f KICKOFF.md && echo OK
  ```
- **Refs:** —

---

### - [ ] Task −1.2 — Install / verify Nix + direnv + Homebrew
- **Files:** none (host setup)
- **Depends on:** −1.1
- **Acceptance:**
  - `nix --version` ≥ 2.18 with flakes enabled (`experimental-features = nix-command flakes` in `~/.config/nix/nix.conf`).
  - `direnv --version` ≥ 2.34 with shell hook in `~/.zshrc` (or active shell rc).
  - `brew --version` present (used later for `cloudflared`, optional `ollama` GUI).
  - Existing `.envrc` allowed: `direnv allow .`
- **Agent commands (check first, install only after asking):**
  ```bash
  nix --version || echo "MISSING: nix"
  direnv --version || echo "MISSING: direnv"
  brew --version || echo "MISSING: brew"
  cat ~/.config/nix/nix.conf 2>/dev/null | grep -q flakes && echo "flakes OK" || echo "MISSING: flakes"
  ```
- **Agent prompt (only if something missing):**
  ```
  I need <tool> installed. The standard macOS install is:

    <install command>

  This will <one-line consequence>. May I run it, or would you prefer
  to install it yourself? (run-it / I'll-do-it / skip)
  ```
- **Verify:**
  ```bash
  nix --version && direnv --version && brew --version
  nix flake show 2>/dev/null | head -5       # confirms flakes work in this repo
  ```
- **Refs:** existing `flake.nix`, `.envrc`

---

### - [ ] Task −1.3 — Verify existing Node + Go toolchains via current flake
- **Files:** none (verification only)
- **Depends on:** −1.2
- **Acceptance:**
  - `nix develop` enters dev shell without error.
  - Inside dev shell: `node --version` ≥ 20.x, `npm --version` present, `go version` ≥ 1.22.
  - `npm install` (or `npm ci` if `package-lock.json` exists) succeeds.
  - `npm run doctor` passes — this is the existing repo healthcheck and MUST pass before we touch anything.
  - `cd dashboard && go build -o /tmp/career-dashboard-test ./...` succeeds.
- **Agent commands:**
  ```bash
  nix develop --command bash -c "node --version && npm --version && go version"
  nix develop --command npm install
  nix develop --command npm run doctor
  nix develop --command bash -c "cd dashboard && go build -o /tmp/career-dashboard-test ./..."
  rm -f /tmp/career-dashboard-test
  ```
- **Blocker conditions:** if `npm run doctor` fails, STOP. Append a Blocker. Do not proceed to Phase 0 — the existing repo must be healthy before extension.
- **Verify:**
  ```bash
  nix develop --command npm run doctor && echo "existing repo healthy"
  ```
- **Refs:** existing `package.json`, `dashboard/`

---

### - [ ] Task −1.4 — Verify Apple Silicon prerequisites
- **Files:** none
- **Depends on:** −1.2
- **Acceptance:**
  - `uname -m` → `arm64` (confirms Apple Silicon — the whole build is M-series-tuned).
  - System has ≥16 GB RAM (`sysctl hw.memsize` → ≥ 17179869184). If 8 GB Mac → BLOCKER (Qwen3-8B will not fit; need swap to Phi-3.8B path; surface to user).
  - `ollama` is installable (will be added to flake in Task 0.1; for now just confirm `brew search ollama` succeeds).
  - Xcode Command Line Tools present: `xcode-select -p` returns a path.
- **Agent commands:**
  ```bash
  uname -m
  sysctl -n hw.memsize | awk '{print $1/1024/1024/1024 " GB RAM"}'
  xcode-select -p || echo "MISSING: xcode-clt — run: xcode-select --install"
  ```
- **Agent prompt (if <16 GB RAM):**
  ```
  ⚠️ Your Mac has <N> GB RAM. The architecture assumes ≥16 GB so we can
  run Qwen3-8B locally for cheap tasks. Options:
    A) Proceed and use the cloud-only path (skip local Ollama, route all
       LLM calls to Claude). Costs more (~$5–8/day extra at 30 apps/day).
    B) Use Phi-3.8B instead of Qwen3-8B (less capable, fits in 8 GB).
    C) Stop and upgrade hardware.
  Which do you want? I will log the decision in BUILD.md.
  ```
- **Verify:**
  ```bash
  uname -m | grep -q arm64 && echo "Apple Silicon OK"
  ```
- **Refs:** arch.C "LLM split"

---

### - [ ] Task −1.5 — Prompt for and store Anthropic API key
- **Files:** none (Keychain only)
- **Depends on:** −1.3
- **Acceptance:**
  - User has an Anthropic API key from console.anthropic.com.
  - Stored in Keychain at service `careerops.anthropic`, account `api_key`.
  - Retrievable via `security find-generic-password -s careerops.anthropic -a api_key -w` (the agent confirms presence by redirecting stdout to `/dev/null` and checking exit code — NEVER printing the value).
- **Agent action:** posts the Secret-Prompt Protocol message (template at top of file). Then waits.
- **Verify:**
  ```bash
  security find-generic-password -s careerops.anthropic -a api_key -w >/dev/null 2>&1 && echo "stored"
  ```
- **Refs:** arch.C "Secrets vault", §🔐 above

---

### - [ ] Task −1.6 — Prompt for Gmail OAuth `client_secret.json` placement
- **Files:** `~/.career-ops/gmail-credentials.json` (outside repo, NEVER committed)
- **Depends on:** −1.3
- **Acceptance:**
  - User has created a Google Cloud project, enabled Gmail API, created an OAuth 2.0 Client ID of type "Desktop application", downloaded `client_secret_*.json`, renamed to `gmail-credentials.json`, and placed at `~/.career-ops/gmail-credentials.json`.
  - Directory permission `0700`, file permission `0600`.
  - Path is outside the git working tree (it lives in `~`, not in the repo).
- **Agent prompt:**
  ```
  🔐 Gmail OAuth setup. Please do these steps in your browser, then come back:

    1. Open: https://console.cloud.google.com/projectcreate
    2. Create project (name it "career-ops" or reuse one you own).
    3. Enable Gmail API:
       https://console.cloud.google.com/apis/library/gmail.googleapis.com
    4. OAuth consent screen → External → Testing → add your own Gmail
       address as a test user.
    5. Credentials → Create Credentials → OAuth client ID
       → Application type: Desktop app → name "career-ops local" → Create.
    6. Download the JSON. Rename to gmail-credentials.json.
    7. In YOUR terminal, run:
         mkdir -p ~/.career-ops && chmod 700 ~/.career-ops
         mv ~/Downloads/gmail-credentials*.json ~/.career-ops/gmail-credentials.json
         chmod 600 ~/.career-ops/gmail-credentials.json

  Note: the actual OAuth refresh token gets stored in Keychain
  AUTOMATICALLY the first time we run `make oauth-gmail` in Task 0.5.
  Today we are only placing the CLIENT secret (not your token).

  Reply "done" when the file is in place. I'll verify.
  ```
- **Verify:**
  ```bash
  test -f ~/.career-ops/gmail-credentials.json && \
    stat -f '%Sp' ~/.career-ops/gmail-credentials.json | grep -q 'rw-------' && \
    echo "OK"
  ```
- **Refs:** arch.G.1

---

### - [ ] Task −1.7 — Verify Keychain round-trip sanity
- **Files:** none
- **Depends on:** −1.5
- **Acceptance:** Round-trip works:
  ```bash
  security add-generic-password -U -s careerops.test -a default -w "ping"
  security find-generic-password -s careerops.test -a default -w | grep -q ping && echo OK
  security delete-generic-password -s careerops.test -a default
  ```
- **Verify:** the round-trip above prints `OK`.
- **Refs:** arch.G.4

---

### - [ ] Task −1.8 — Final cold-start checkpoint
- **Files:** BUILD.md (status block only)
- **Depends on:** −1.1 through −1.7
- **Acceptance:** Agent posts a single summary to the user:
  ```
  Cold-start checklist:
    ✓ Repo cloned at <path>
    ✓ Branch feat/autonomous-applier checked out
    ✓ Nix + direnv + Homebrew verified
    ✓ Existing Node + Go stack passes `npm run doctor`
    ✓ Apple Silicon confirmed, <N> GB RAM
    ✓ Anthropic API key stored in Keychain
    ✓ Gmail client_secret.json placed at ~/.career-ops/
    ✓ Keychain round-trip works

  Ready to start Phase 0 (Foundations). First task: 0.1 — extend flake.nix
  with Python 3.12 + uv + Playwright + Ollama.

  Proceed? (yes/no)
  ```
- **Verify:** user replies "yes."
- **Refs:** —

---

## 📋 Phase 0 — Foundations (Week 1, no behavior change)

**Phase goal:** Add Python toolchain alongside existing Node.js/Go stack. Implement secrets vault wrapper, Gmail OAuth, FastAPI scaffold, SQLite schema, autonomy doc. Zero changes to existing applier behavior. The existing `modes/apply.md` HITL contract remains in force.

**Phase exit criteria:** `nix develop --command bash -c "uv run python -c 'from agents.tools.keychain import get_secret; from agents.tools.gmail import get_service'"` works. `npm run doctor` still passes. `bridge/server.py` serves `GET /health`. No applier code touched yet.

---

### - [ ] Task 0.1 — Extend `flake.nix` with Python 3.12 + uv + Playwright system deps + Ollama
- **Files:** `flake.nix`, `flake.lock`
- **Depends on:** −1.8
- **Acceptance:**
  - `nix develop` provides `python3.12`, `uv`, `node`, `go`, `ollama`, plus Playwright system libs (`nss`, `nspr`, `at-spi2-atk`, `cups`, etc.) on `$PATH`.
  - `flake.lock` regenerated and committed.
  - Existing Node + Go tooling still works (`npm run doctor` passes).
  - **Important:** Add Python via `mkShell` inputs, NOT by replacing the existing shell — preserve everything currently provided.
- **Verify:**
  ```bash
  nix develop --command bash -c "python --version | grep -q 3.12 && uv --version && ollama --version && node --version && go version && npm run doctor"
  ```
- **Refs:** arch.D Phase 0 step 1

---

### - [x] ✅ 2026-05-15 Task 0.2 — Create Python scaffold + `.gitignore`
- **Files:** `agents/__init__.py`, `agents/{orchestrator,workers,tools,adapters,prompts,tests}/__init__.py`, `bridge/__init__.py`, `audit/.gitkeep`, `db/.gitkeep`, `cv/.gitkeep`, `infra/.gitkeep`, `scripts/.gitkeep`, `bin/.gitkeep`, `docs/.gitkeep`, `.gitignore` (extend)
- **Depends on:** 0.1
- **Acceptance:**
  - Directory tree matches the "Folder layout" table above.
  - `.gitignore` additions (append, do not replace existing):
    ```
    # Python
    __pycache__/
    *.pyc
    .venv/
    .python-version

    # uv
    .uv/

    # Project runtime artifacts
    output/*.pdf
    output/*.html
    audit/
    db/careerops.db
    db/careerops.db-*
    !db/.gitkeep
    !audit/.gitkeep

    # Browser persistent contexts (live in ~/Library — but defensive)
    browser-context/

    # Secrets / OAuth
    .env
    .env.*
    !.env.example
    *credentials*.json
    *.session
    storage_state.json

    # Test artifacts
    playwright-report/
    test-results/
    .pytest_cache/
    .mypy_cache/
    .ruff_cache/

    # Editor
    .idea/
    .vscode/
    *.swp
    ```
- **Verify:**
  ```bash
  ls agents/{orchestrator,workers,tools,adapters,prompts,tests} bridge audit db cv infra scripts bin docs
  git check-ignore audit/anything output/foo.pdf db/careerops.db .env >/dev/null && echo "ignores OK"
  ```
- **Refs:** "Folder layout" above

---

### - [x] ✅ 2026-05-15 Task 0.3 — `pyproject.toml` + initial `uv sync`
- **Files:** `pyproject.toml`, `uv.lock`, `.python-version`
- **Depends on:** 0.2
- **Acceptance:**
  - `pyproject.toml` declares:
    - `requires-python = ">=3.12,<3.13"` (exact 3.12 line; 3.13 has scattered package compatibility issues as of this writing).
    - Runtime deps: `langgraph>=0.4`, `langchain-anthropic`, `langchain-ollama`, `playwright>=1.49`, `playwright-stealth>=2.0.2`, `anthropic>=0.40`, `keyring>=25.7`, `google-api-python-client`, `google-auth-oauthlib`, `httpx`, `fastapi`, `uvicorn[standard]`, `pysqlcipher3`, `sqlite-vec`, `nanoid`, `structlog`, `pydantic>=2`, `python-dotenv`, `tenacity`.
    - Dev deps: `pytest`, `pytest-asyncio`, `pytest-mock`, `ruff`, `mypy`, `types-requests`.
    - `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]` blocks.
  - `.python-version` → `3.12`.
  - `uv sync` succeeds; `uv run playwright install chromium` succeeds.
  - `uv.lock` committed.
- **Verify:**
  ```bash
  nix develop --command bash -c "uv sync && uv run playwright install --with-deps chromium && uv run python --version | grep 3.12 && uv run pytest --version"
  ```
- **Refs:** arch.C tech stack table

---

### - [x] ✅ 2026-05-15 Task 0.4 — `agents/tools/keychain.py` with macOS Keychain + 1Password CLI fallback
- **Files:** `agents/tools/keychain.py`, `agents/tests/test_keychain.py`, `docs/SECRETS.md`
- **Depends on:** 0.3
- **Acceptance:**
  - Functions: `get_secret(name, account="default")`, `set_secret(name, value, account="default")`, `delete_secret(name, account="default")`, plus convenience accessors (`claude_api_key`, `capsolver_key`, `whatsapp_token`, `site_password(site)`).
  - `CAREEROPS_VAULT` env var switches backend: `keychain` (default), `op`, `bw`.
  - All service names prefixed `careerops.`
  - Unit test: round-trip set/get/delete with monkeypatched `keyring` backend.
  - `docs/SECRETS.md` documents Keychain Access.app step for tightening per-binary ACLs (the `jaraco/keyring` #457 mitigation).
- **Verify:**
  ```bash
  uv run pytest agents/tests/test_keychain.py -v
  uv run python -c "from agents.tools.keychain import get_secret; print(get_secret('does_not_exist'))"
  ```
- **Refs:** arch.G.4, arch.E.1

---

### - [x] ✅ 2026-05-15 Task 0.5 — `agents/tools/gmail.py` (OAuth2 + verification-code extractor)
- **Files:** `agents/tools/gmail.py`, `agents/tests/test_gmail.py` (mocked), `docs/GMAIL_SETUP.md`, `Makefile` with `oauth-gmail` target
- **Depends on:** 0.4
- **Acceptance:**
  - Scopes: `gmail.readonly` + `gmail.modify` ONLY (NO send, NO full mail).
  - Functions: `get_service()`, `search(query, max_results)`, `get_body_text(msg_id)`, `mark_read(msg_id)`, `get_verification_code(sender_domain, poll_seconds, interval, newer_than)`.
  - Refresh token sealed in Keychain via `keychain.set_secret("gmail", token_json, "oauth_token_json")`.
  - `docs/GMAIL_SETUP.md` references the steps already executed in Task −1.6 + the `make oauth-gmail` command.
  - `make oauth-gmail` runs `uv run python -m agents.tools.gmail` and prompts the browser consent on first run.
- **Verify:**
  ```bash
  uv run pytest agents/tests/test_gmail.py -v
  # After manual oauth:
  make oauth-gmail
  uv run python -c "from agents.tools.gmail import get_service; print(get_service().users().getProfile(userId='me').execute()['emailAddress'])"
  ```
- **Refs:** arch.G.1

---

### - [x] ✅ 2026-05-15 Task 0.6 — FastAPI bridge scaffold at `127.0.0.1:8765`
- **Files:** `bridge/server.py`, `bridge/__main__.py`, `agents/tests/test_bridge_health.py`
- **Depends on:** 0.3
- **Acceptance:**
  - `GET /health` returns `{"ok": true, "version": "<git-sha>"}`.
  - Server binds `127.0.0.1` only (NEVER `0.0.0.0`).
  - `uv run python -m bridge` starts uvicorn on port 8765.
  - No endpoints beyond `/health` yet — `/run`, `/internal/request_approval`, `/webhook/whatsapp`, `/approve` arrive in Task 1.7.
- **Verify:**
  ```bash
  uv run python -m bridge &
  sleep 2 && curl -s http://127.0.0.1:8765/health | jq -e '.ok == true'
  pkill -f "python -m bridge"
  ```
- **Refs:** arch.B.1, arch.C "Local control plane"

---

### - [x] ✅ 2026-05-15 Task 0.7 — SQLite schema + migration script
- **Files:** `db/schema.sql`, `db/migrate.py`, `db/migrations/0001_init.sql`, `agents/tests/test_schema.py`
- **Depends on:** 0.3
- **Acceptance:**
  - Tables per arch.D.6: `runs`, `checkpoints`, `actions`, `approvals`, `jd_embeddings`.
  - `db/migrate.py` creates fresh `db/careerops.db` if missing, applies pending migrations idempotently.
  - Indexes: `runs(jd_id)`, `runs(status)`, `actions(run_id, ts)`, `approvals(decision)`.
  - Test inserts a sample run and asserts retrieval.
  - NOT SQLCipher-encrypted yet (that is Task 5.1).
- **Verify:**
  ```bash
  uv run python -m db.migrate && uv run pytest agents/tests/test_schema.py -v
  sqlite3 db/careerops.db ".tables" | grep -q runs && echo OK
  ```
- **Refs:** arch.D.6

---

### - [x] ✅ 2026-05-15 Task 0.8 — `docs/AUTONOMY.md` + update `CLAUDE.md` and `LEGAL_DISCLAIMER.md`
- **Files:** `docs/AUTONOMY.md`, `CLAUDE.md` (append section, do not rewrite), `LEGAL_DISCLAIMER.md` (append section), `config/profile.yml` (add `autonomy:` block)
- **Depends on:** —
- **Acceptance:**
  - `docs/AUTONOMY.md` documents the 0–4 autonomy ladder per arch.D Phase 4 (`0=dry-run, 1=approve-everything, 2=approve-submit-only, 3=approve-anomalies-only, 4=full-auto`) with the rules table.
  - `CLAUDE.md` gets a new "Autonomous Mode" section explaining that any agent running the applier must always pass through `request_human_approval` until autonomy ≥ N for that gate. Add one line near the top: *"Build progress lives in `BUILD.md`. Read it at session start and follow its Update Protocol."*
  - `LEGAL_DISCLAIMER.md` adds explicit warnings on LinkedIn/Workday automation, per-site rate caps, and the "one human, one identity" principle (arch.E.2).
  - `config/profile.yml` gets an `autonomy:` block with `level: 1` (start conservative even after Phase 4 ships) and `rules:` matching the arch doc.
- **Verify:** Manual review. Confirm `grep -c "autonomy_level" CLAUDE.md` ≥ 1 and `grep -c "BUILD.md" CLAUDE.md` ≥ 1.
- **Refs:** arch.D Phase 4, arch.E.2

---

## 📋 Phase 1 — MVP: Single-Site Applier with Maximum HITL (Weeks 2–3)

**Phase goal:** Apply to ONE Greenhouse job end-to-end with HITL gates at PDF approval, account creation, 2FA, and final submit. Autonomy level 1 — every gate fires WhatsApp.

**Phase exit criteria:** 3 real Greenhouse jobs applied end-to-end with HITL at every gate. Zero submissions without explicit user approval. All artifacts (PDFs, screenshots, audit rows) generated and stored.

---

### - [x] ✅ 2026-05-15 Task 1.1 — LangGraph orchestrator skeleton with `SqliteSaver`
- **Files:** `agents/orchestrator/graph.py`, `agents/orchestrator/state.py`, `agents/tests/test_graph_smoke.py`
- **Depends on:** 0.7, 0.6
- **Acceptance:**
  - `AppState` TypedDict per arch.G.3 (`run_id`, `jd_id`, `jd_url`, `jd_text`, `track`, `score`, `report_path`, `pdf_path`, `cover_path`, `ats_family`, `autonomy_level`, `errors`, `gate_pending`, `screenshot_path`).
  - Nodes: `score`, `tailor`, `pdf_gate`, `apply`, `verify`. Conditional edge after `score` ends graph if score < 4.0.
  - `SqliteSaver` checkpointer pointed at `db/careerops.db`.
  - Smoke test runs the graph with stub worker functions returning canned values; asserts checkpoint row written.
- **Verify:**
  ```bash
  uv run pytest agents/tests/test_graph_smoke.py -v
  ```
- **Refs:** arch.G.3, arch.B.4

---

### - [ ] Task 1.2 — Scorer worker (`agents/workers/scorer.py`)
- **Files:** `agents/workers/scorer.py`, `agents/prompts/scorer.md`, `agents/tests/test_scorer.py`, `cv/da.md`, `cv/mle.md`, `cv/de.md` (stub starting files)
- **Depends on:** 1.1
- **Acceptance:**
  - System prompt at `agents/prompts/scorer.md` is exactly arch.F.3.
  - `score_jd(jd_text) -> dict` returns `{track, score, subscores, dimensions, rationale, kill_signals, tailor_keywords, report_path}`.
  - Uses Claude Sonnet 4.5 via `langchain-anthropic` (API key from Keychain).
  - Writes report markdown to `reports/{NNN}-{slug}-{date}.md` matching existing repo conventions.
  - Kill-signal heuristic: explicit "no sponsorship + sponsorship required" mismatch from `profile.yml`, comp below floor, locations outside allowed list, deal-breaker keywords.
  - CV stub files contain placeholder sections the user fills in.
  - Test uses fixture JD + mocked Anthropic client; asserts score in [1, 5] and track ∈ {DA, MLE, DE}.
- **Verify:**
  ```bash
  uv run pytest agents/tests/test_scorer.py -v
  ```
- **Refs:** arch.F.3, arch.A "ATS scoring" row

---

### - [ ] Task 1.3 — Tailor worker (subprocess to existing `generate-pdf.mjs`)
- **Files:** `agents/workers/tailor.py`, `agents/prompts/tailor.md`, `agents/tests/test_tailor.py`
- **Depends on:** 1.2
- **Acceptance:**
  - System prompt at `agents/prompts/tailor.md` is exactly arch.F.4.
  - `tailor_resume(jd_text, track, run_id) -> {pdf_path, cover_path, diff_summary}`.
  - Calls existing `generate-pdf.mjs` via `subprocess.run(["node", "generate-pdf.mjs", "--input", md_path, "--output", pdf_path])`.
  - Cover letter uses web search for 2–3 recent company facts.
  - HARD RULE enforced in prompt + post-hoc check: no skill, company name, date, or number added that is not in the user's `cv/{track}.md`.
  - Outputs land at `output/{run_id}.pdf` and `output/{run_id}-cover.md`.
- **Verify:**
  ```bash
  uv run pytest agents/tests/test_tailor.py -v
  test -f output/test-run-001.pdf
  ```
- **Refs:** arch.F.4

---

### - [ ] Task 1.4 — Greenhouse adapter (`agents/adapters/ats_greenhouse.py`)
- **Files:** `agents/adapters/__init__.py` (with `REGISTRY` dict), `agents/adapters/ats_greenhouse.py`, `agents/adapters/base.py`, `agents/tests/test_adapter_greenhouse.py` (with HAR fixture)
- **Depends on:** 1.6 (browser harness)
- **Acceptance:**
  - `REGISTRY = {"greenhouse": Greenhouse, "lever": ..., ...}` pattern.
  - `base.py` defines `class ATSAdapter` with `async def run(page, *, pdf_path, profile, cover_text, run_id, human_type, approve, screenshot) -> dict`.
  - Greenhouse impl fills `#first_name`, `#last_name`, `#email`, `#phone`, uploads to `#resume`, fills `#cover_letter` if present, handles EEO + work-auth dropdowns from `profile.yml`.
  - Adapter NEVER clicks the final submit button itself — that is the harness's job after `approve()` returns "approved".
  - Test uses Playwright `route()` to serve a recorded HAR of a real Greenhouse form; asserts all fields populated and submit not clicked.
- **Verify:**
  ```bash
  uv run pytest agents/tests/test_adapter_greenhouse.py -v
  ```
- **Refs:** arch.G.5 (end of file)

---

### - [ ] Task 1.5 — WhatsApp tool + Meta Cloud API setup
- **Files:** `agents/tools/whatsapp.py`, `docs/WHATSAPP_SETUP.md`, `agents/tests/test_whatsapp.py` (mocked HTTP)
- **Depends on:** 0.4
- **Acceptance:**
  - Functions: `send_text(text) -> str`, `send_image_with_caption(image_path, caption) -> str`. Token from Keychain `careerops.whatsapp/access_token`.
  - Implementation matches arch.G.2 exactly.
  - `docs/WHATSAPP_SETUP.md` covers: Meta for Developers → Business app → WhatsApp product → permanent token → set env vars `WA_PHONE_NUMBER_ID`, `WA_USER_NUMBER`, `WA_WEBHOOK_VERIFY_TOKEN` → Cloudflare Tunnel install (`brew install cloudflared`) → tunnel pointing to `127.0.0.1:8765/webhook/whatsapp`.
  - Test mocks `httpx.post` and asserts payload shape.
- **Verify:**
  ```bash
  uv run pytest agents/tests/test_whatsapp.py -v
  # Manual: after env vars + Keychain set:
  uv run python -c "from agents.tools.whatsapp import send_text; send_text('🤖 career-ops alive')"
  ```
- **Refs:** arch.G.2, arch.C "WhatsApp HITL"

---

### - [ ] Task 1.6 — Browser harness (Playwright + Computer Use hybrid)
- **Files:** `agents/tools/browser_harness.py`, `agents/tools/computer_use.py`, `agents/tests/test_harness_stealth.py`
- **Depends on:** 0.3
- **Acceptance:**
  - Implementation matches arch.G.5 exactly.
  - `open_persistent(site_key)` creates `~/Library/Application Support/career-ops/browser/{site}` with `0700` perms.
  - `detect_ats(page)` returns one of: `greenhouse`, `lever`, `ashby`, `workday`, `linkedin`, `indeed`, `generic`.
  - `human_type(page, selector, text)` types with 70–130 ms variable per-char delay + 0.4–0.8 s tail.
  - `screenshot(page, label, run_id)` writes to `audit/{run_id}/{ts}-{label}.png`.
  - `computer_use_step(page, instruction, run_id)` calls Claude Sonnet 4.5 with `computer_20250124` tool.
  - `apply_to_url(...)` calls `approval_callback("final_submit", ...)` before any submit click.
  - Stealth test asserts `navigator.webdriver === undefined` after `Stealth.apply_stealth_async`.
- **Verify:**
  ```bash
  uv run pytest agents/tests/test_harness_stealth.py -v
  ```
- **Refs:** arch.G.5, arch.C.1

---

### - [ ] Task 1.7 — Bridge endpoints: `/run`, `/state/{run_id}`, `/internal/request_approval`, `/webhook/whatsapp`, `/approve/{run_id}`, `/reject/{run_id}`
- **Files:** `bridge/server.py` (extend), `bridge/approvals.py`, `agents/tests/test_bridge_approvals.py`
- **Depends on:** 1.1, 1.5
- **Acceptance:**
  - `POST /run` accepts `{jd_id}`, launches orchestrator graph in background task with `thread_id=run_id`, returns `{run_id}`.
  - `GET /state/{run_id}` returns latest checkpoint state from `SqliteSaver`.
  - `POST /internal/request_approval` matches arch.G.2 (blocks until WhatsApp reply or timeout).
  - `GET /webhook/whatsapp` (Meta verification) + `POST /webhook/whatsapp` (inbound replies) wire to `APPROVALS_WAITING` futures.
  - `POST /approve/{run_id}` / `POST /reject/{run_id}` provide a manual override path from CLI/TUI when WhatsApp is unreachable.
  - `APPROVALS_WAITING` survives a server restart by re-reading `approvals` table on startup (best-effort — runs that were mid-flight get marked `paused`).
  - Test: integration test with TestClient asserts full approval cycle (request → mock inbound webhook → future resolves to `approved`).
- **Verify:**
  ```bash
  uv run pytest agents/tests/test_bridge_approvals.py -v
  ```
- **Refs:** arch.G.2, arch.E.4

---

### - [ ] Task 1.8 — Rewrite `modes/apply.md` as dispatcher to bridge
- **Files:** `modes/apply.md` (rewrite, preserving existing front-matter), `bin/career-apply`, `agents/tests/test_apply_dispatcher.py`
- **Depends on:** 1.7
- **Acceptance:**
  - New `modes/apply.md` mode is a Claude Code skill that, given a JD URL or `jd_id`:
    1. Confirms `bridge/server` is running (else instructs user to `uv run python -m bridge`).
    2. `POST /run` with the JD.
    3. Streams `/state/{run_id}` updates back to the user.
    4. NEVER directly drives a browser itself.
  - Existing 14-mode contract preserved: front-matter, mode name, description fields.
  - `modes/_shared.md` updated to reference the Python orchestrator instead of inline form-filling guidance.
  - Bash helper `bin/career-apply <jd_id>` wraps the dispatcher for non-Claude-Code use.
- **Verify:** Manual — run `claude /apply <jd_id>` against a test fixture; confirm dispatcher path.
- **Refs:** arch.A "Files to extend" → `modes/apply.md` row

---

### - [ ] Task 1.9 — Migrate `data/applications.md` schema (add columns)
- **Files:** `data/applications.md` (extend headers), `scripts/migrate-applications-md.mjs` (new), `templates/states.yml` (add canonical statuses), `normalize-statuses.mjs` (update)
- **Depends on:** 0.8
- **Acceptance:**
  - New columns appended (NOT inserted mid-table — preserves `DATA_CONTRACT.md` user-edits): `apply_status`, `apply_run_id`, `track`, `gate_log`, `screenshot_dir`.
  - `templates/states.yml` adds: `apply_queued`, `apply_in_progress`, `awaiting_2fa`, `awaiting_approval`, `submitted`, `apply_failed`.
  - `scripts/migrate-applications-md.mjs` is idempotent — running twice is a no-op.
  - `normalize-statuses.mjs` validates the new states without complaining.
- **Verify:**
  ```bash
  node scripts/migrate-applications-md.mjs && node scripts/migrate-applications-md.mjs   # idempotent
  npm run doctor   # still passes
  ```
- **Refs:** arch.A "Files to extend"

---

## 📋 Phase 2 — Multi-Site Coverage (Weeks 4–6)

**Phase goal:** Adapters for Lever, Ashby, Workday, Indeed/Glassdoor, Wellfound, LinkedIn Easy Apply, and a generic Computer-Use fallback. CAPTCHA wiring. All gated by HITL.

**Phase exit criteria:** ≥1 successful HITL-gated submission per source family. Per-adapter HAR fixture tests passing.

---

### - [ ] Task 2.1 — Lever adapter
- **Files:** `agents/adapters/ats_lever.py`, `agents/tests/fixtures/lever.har`, `agents/tests/test_adapter_lever.py`
- **Depends on:** 1.4
- **Acceptance:** Stable Lever form selectors (`input[name="name"]`, `input[name="email"]`, etc.); resume upload; submit gated by `approve()`. Test serves HAR fixture and asserts field population.
- **Verify:** `uv run pytest agents/tests/test_adapter_lever.py -v`
- **Refs:** arch.C.1 "Greenhouse/Lever/Ashby" row

---

### - [ ] Task 2.2 — Ashby adapter
- **Files:** `agents/adapters/ats_ashby.py`, `agents/tests/fixtures/ashby.har`, `agents/tests/test_adapter_ashby.py`
- **Depends on:** 1.4
- **Acceptance:** Ashby GraphQL for listing fetch (Scanner side); for application form, Playwright drives the standard React form. Submit gated.
- **Verify:** `uv run pytest agents/tests/test_adapter_ashby.py -v`
- **Refs:** arch.C.1

---

### - [ ] Task 2.3 — Workday adapter (multi-page wizard + Computer Use fallback)
- **Files:** `agents/adapters/ats_workday.py`, `agents/adapters/_workday_fields.py` (field-family map), `agents/tests/fixtures/workday_*.har`, `agents/tests/test_adapter_workday.py`
- **Depends on:** 1.4, 1.6
- **Acceptance:**
  - Multi-page wizard support (My Information → My Experience → Application Questions → Voluntary Disclosures → Review → Submit).
  - Persistent context per Workday tenant subdomain (each company is its own URL).
  - Field-family selectors via `[data-automation-id*='...']`. When no deterministic match: fall back to `computer_use_step`.
  - Per-tenant delay: 1500–3500 ms inter-action.
  - Submit gated by `approve()`.
- **Verify:** `uv run pytest agents/tests/test_adapter_workday.py -v`
- **Refs:** arch.C.1, arch.E.1 Workday row

---

### - [ ] Task 2.4 — Indeed + Glassdoor adapters
- **Files:** `agents/adapters/ats_indeed.py`, `agents/adapters/ats_glassdoor.py`, fixtures + tests
- **Depends on:** 1.4, 2.8 (captcha)
- **Acceptance:** Indeed Easy Apply + Glassdoor Easy Apply. Cloudflare Turnstile detected → solver via Task 2.8. Per-day cap ≤ 15 Indeed.
- **Verify:** `uv run pytest agents/tests/test_adapter_indeed.py agents/tests/test_adapter_glassdoor.py -v`
- **Refs:** arch.C.1, arch.E.1

---

### - [ ] Task 2.5 — Wellfound adapter
- **Files:** `agents/adapters/ats_wellfound.py`, fixture + test
- **Depends on:** 1.4
- **Acceptance:** Treats Wellfound like Greenhouse (standard form, minimal stealth). Submit gated.
- **Verify:** `uv run pytest agents/tests/test_adapter_wellfound.py -v`
- **Refs:** arch.C.1

---

### - [ ] Task 2.6 — LinkedIn Easy Apply adapter
- **Files:** `agents/adapters/ats_linkedin.py`, `docs/LINKEDIN_SESSION.md`, `scripts/save-linkedin-session.mjs`, fixture + test
- **Depends on:** 1.4, 1.6
- **Acceptance:**
  - Pre-existing logged-in session via Playwright `storage_state.json`, captured manually by user once (script in `scripts/save-linkedin-session.mjs`).
  - Operates only on Easy Apply modal (`[data-test-modal]` / `.jobs-easy-apply-modal`).
  - **No profile scraping. No data extraction. No fake-account creation. Ever.**
  - Per-source cap: ≤8/hr, ≤25/day (rate limiter Task 3.6).
  - On any "restricted" / "verify you're human" page → halt LinkedIn source globally for 60 min; WhatsApp critical alert.
  - `docs/LINKEDIN_SESSION.md` walks the user through manual login + session save once.
- **Verify:** `uv run pytest agents/tests/test_adapter_linkedin.py -v`
- **Refs:** arch.C.1 LinkedIn row, arch.E.1 LinkedIn row, arch.E.2

---

### - [ ] Task 2.7 — Generic Computer-Use fallback adapter
- **Files:** `agents/adapters/ats_generic.py`, `agents/tests/test_adapter_generic.py`
- **Depends on:** 1.6
- **Acceptance:** Vision-first walkthrough using `computer_use_step` for arbitrary career-page forms. Hard cap: max 8 vision steps per page before `approve("anomaly")` escalates. Submit gated.
- **Verify:** `uv run pytest agents/tests/test_adapter_generic.py -v`
- **Refs:** arch.C.1 generic row

---

### - [ ] Task 2.8 — CAPTCHA integration (CapSolver primary, 2Captcha fallback)
- **Files:** `agents/tools/captcha.py`, `agents/tests/test_captcha.py`
- **Depends on:** 0.4
- **Acceptance:**
  - `captcha_solve(type, site_key, page_url) -> token`. Types: `recaptcha_v2`, `recaptcha_v3`, `turnstile`, `hcaptcha`.
  - CapSolver tried first; 2Captcha fallback on failure. API keys from Keychain.
  - On 2nd consecutive failure for same `run_id` → raise `CaptchaEscalateError` → harness calls `approve("captcha", ...)`.
  - Budget guard: per-day spend cap from `profile.yml` (default $1/day). On hit → halt that source.
  - Mock test for both services.
- **Verify:** `uv run pytest agents/tests/test_captcha.py -v`
- **Refs:** arch.C "CAPTCHA"

---

## 📋 Phase 3 — Volume & Verifier (Weeks 7–8)

**Phase goal:** Replace parts of `scan.mjs` with Python `scanner.py`. Add `verifier.py` for confirmation-email + DOM checks. Embedding-based scoring. Three CV tracks. Daily scheduling. Rate limiter.

**Phase exit criteria:** 20+ applications/day for 5 consecutive days. Zero ban signals. Zero unintended submissions.

---

### - [ ] Task 3.1 — Scanner worker (Greenhouse/Lever JSON + Ashby GraphQL + LinkedIn public)
- **Files:** `agents/workers/scanner.py`, `agents/prompts/scanner.md`, `agents/tests/test_scanner.py`
- **Depends on:** 1.1
- **Acceptance:**
  - Prompt at `agents/prompts/scanner.md` is exactly arch.F.2.
  - Functions: `scan_greenhouse(company_slugs)`, `scan_lever(...)`, `scan_ashby(...)`, `scan_linkedin_public(queries)`, `scan_company_pages(urls)`.
  - LinkedIn public scan only (logged-out, JDs only); no login.
  - Dedup via `data/scan-history.tsv` hash `(company_slug, role_title, location)`.
  - Writes JD body to `jds/{jd_id}.txt`, appends row to `data/pipeline.md`.
  - Max 200 new JDs per run; respects per-source 429 backoff.
- **Verify:** `uv run pytest agents/tests/test_scanner.py -v`
- **Refs:** arch.F.2

---

### - [ ] Task 3.2 — Verifier worker (Gmail polling + DOM post-submit check)
- **Files:** `agents/workers/verifier.py`, `agents/prompts/verifier.md`, `agents/tools/llm_local.py`, `agents/tests/test_verifier.py`
- **Depends on:** 0.5, 1.6
- **Acceptance:**
  - Polls Gmail for ≤10 min with `q="from:(...) newer_than:1h"` for known ATS confirmation senders.
  - Classifies each hit with local Phi-4 / Gemma3 via Ollama (`agents/tools/llm_local.py` shim) as `confirmation | rejection | newsletter`.
  - Re-loads `jd_url` and looks for post-submit DOM markers: "Thanks for applying", "Application received", confirmation URL.
  - Writes evidence to `audit/{run_id}/verifier/` and updates `applications.md` row status.
- **Verify:** `uv run pytest agents/tests/test_verifier.py -v`
- **Refs:** arch.F.6

---

### - [ ] Task 3.3 — Embeddings + `sqlite-vec` for semantic similarity
- **Files:** `agents/tools/embeddings.py`, `db/migrations/0002_jd_embeddings_index.sql`, `agents/tests/test_embeddings.py`
- **Depends on:** 0.7, 1.2
- **Acceptance:**
  - `embed_text(text) -> list[float]` uses `nomic-embed-text` via Ollama (768-d).
  - Stored in `jd_embeddings` table; queried with `sqlite-vec` KNN.
  - Scorer extension: replace the placeholder `semantic_sim` with real cosine.
- **Verify:** `uv run pytest agents/tests/test_embeddings.py -v`
- **Refs:** arch.B.4, arch.F.3

---

### - [ ] Task 3.4 — Three CV tracks (`cv/da.md`, `cv/mle.md`, `cv/de.md`)
- **Files:** `cv/da.md`, `cv/mle.md`, `cv/de.md`, `cv/README.md`, `docs/CV_TRACKS.md`
- **Depends on:** 1.3
- **Acceptance:**
  - Each track has: header, summary, skills, experience bullets (organized by role), education, projects, certifications.
  - `cv/README.md` documents how the user authors them and how the Tailor agent reads them.
  - Tailor agent uses the track selected by Scorer.
  - User-facing: this is the file the user actually edits — the agent does not write here, only reads.
- **Verify:** Manual — user reviews and fills the stub files.
- **Refs:** arch.D Phase 3 step 4

---

### - [ ] Task 3.5 — `launchd` plist for daily 09:00 scan + apply
- **Files:** `infra/com.career-ops.daily.plist`, `infra/install-launchd.sh`, `bin/career-ops-daily`, `docs/SCHEDULING.md`
- **Depends on:** 3.1
- **Acceptance:**
  - Plist runs `bin/career-ops-daily` at 09:00 local time on weekdays.
  - Daily script: scan → score → tailor candidates with score ≥ 4.0 → enqueue applies (HITL still required).
  - `infra/install-launchd.sh` copies plist to `~/Library/LaunchAgents/` and loads it.
  - `docs/SCHEDULING.md` covers `launchctl load/unload`, log locations, troubleshooting.
- **Verify:**
  ```bash
  bash infra/install-launchd.sh
  launchctl list | grep -q com.career-ops.daily && echo OK
  ```
- **Refs:** arch.D Phase 3 step 5

---

### - [ ] Task 3.6 — Rate limiter (per-source caps + gaussian inter-arrival)
- **Files:** `agents/tools/rate_limiter.py`, `agents/tests/test_rate_limiter.py`
- **Depends on:** 0.7
- **Acceptance:**
  - Per-source caps in `config/profile.yml`: `linkedin: 8/hr, 25/day`; `indeed: 5/hr, 15/day`; default `8/hr, 25/day`. Global `50/day`.
  - Gaussian inter-arrival between applies: µ=180 s σ=60 s (clamp 60–600 s).
  - Quiet hours 22:00–08:00 (user override).
  - On cap hit: pause that source; on global hit: pause all applies.
  - State persisted in SQLite so caps survive restart.
- **Verify:** `uv run pytest agents/tests/test_rate_limiter.py -v`
- **Refs:** arch.E.3 cadence row

---

## 📋 Phase 4 — Easing into Autonomy (Weeks 9–12)

**Phase goal:** Implement the autonomy ladder. Auto-pass safe gates. Anomaly detector. Weekly digest.

**Phase exit criteria:** Autonomy level 2 stable for 7 days. Anomaly detector tested on 20+ varied JDs. Digest delivered 2 consecutive Sundays.

---

### - [ ] Task 4.1 — Autonomy ladder enforcement in orchestrator
- **Files:** `agents/orchestrator/autonomy.py`, `agents/tests/test_autonomy.py`, `config/profile.yml` (extend rules)
- **Depends on:** 1.1, 0.8
- **Acceptance:** Levels 0–4 honored. Rules table from arch.D Phase 4 fully implemented. Level read from `profile.yml` on each run.
- **Verify:** `uv run pytest agents/tests/test_autonomy.py -v`
- **Refs:** arch.D Phase 4

---

### - [ ] Task 4.2 — Auto-pass rules (submit-gate auto when score ≥ 4.5 AND known ATS AND no free-text Qs)
- **Files:** `agents/orchestrator/auto_pass.py`, `agents/tests/test_auto_pass.py`
- **Depends on:** 4.1, 4.3
- **Acceptance:** All four conditions must hold: `score ≥ 4.5` AND `ats_family ∈ {greenhouse,lever,ashby}` AND `anomaly_score < 0.2` AND `verifier_dry_run() == ok`.
- **Verify:** `uv run pytest agents/tests/test_auto_pass.py -v`
- **Refs:** arch.D Phase 4 step 1

---

### - [ ] Task 4.3 — Anomaly detector (form has unusual free-text questions)
- **Files:** `agents/workers/anomaly.py`, `agents/tests/test_anomaly.py`
- **Depends on:** 1.6
- **Acceptance:** Pre-submit pass over rendered form. Detects: free-text > 200 chars expected, "Why this company?" pattern, custom screening questions, video upload requests, work-sample requests. Returns `anomaly_score ∈ [0,1]` and per-issue list. ≥ 0.5 forces HITL even at autonomy 4.
- **Verify:** `uv run pytest agents/tests/test_anomaly.py -v`
- **Refs:** arch.D Phase 4 step 2

---

### - [ ] Task 4.4 — Weekly WhatsApp digest (Sunday 18:00 local)
- **Files:** `agents/workers/digest.py`, `infra/com.career-ops.weekly.plist`, `agents/tests/test_digest.py`
- **Depends on:** 1.5, 3.5
- **Acceptance:** Sunday 18:00 launchd job. Sends WhatsApp summary: apps sent this week, response rate, anomalies queued for batch review, top 3 highest-scoring rejected (recovery candidates), this week's CAPTCHA + API spend.
- **Verify:** `uv run pytest agents/tests/test_digest.py -v`
- **Refs:** arch.D Phase 4 step 3

---

## 📋 Phase 5 — Hardening (Weeks 13+)

**Phase goal:** Encryption at rest, screenshot redaction, circuit breakers, session healthchecks, observability in the existing Go TUI.

---

### - [ ] Task 5.1 — SQLCipher encryption for `db/careerops.db`
- **Files:** `db/migrate.py` (extend), `agents/tools/db.py`, `agents/tests/test_db_encryption.py`, `docs/ENCRYPTION.md`
- **Depends on:** 0.7
- **Acceptance:** Encryption key from Keychain `careerops.db/encryption_key`. Connection wrapper sets `PRAGMA key`. Existing tables migrated to encrypted DB on first run.
- **Verify:** `uv run pytest agents/tests/test_db_encryption.py -v`
- **Refs:** arch.B.6, arch.E.1

---

### - [ ] Task 5.2 — Screenshot redaction (regex + lightweight OCR for SSN/salary/DOB)
- **Files:** `agents/tools/redact.py`, `agents/tests/test_redact.py`
- **Depends on:** 1.6
- **Acceptance:** Pre-save pass over screenshots: detects fields tagged `sensitive` in `modes/_shared.md`; black-boxes the rectangle. OCR via `pytesseract` for free-form text fields containing SSN-shaped or currency-shaped strings.
- **Verify:** `uv run pytest agents/tests/test_redact.py -v`
- **Refs:** arch.B.6

---

### - [ ] Task 5.3 — Per-adapter circuit breakers
- **Files:** `agents/tools/circuit.py`, `agents/tests/test_circuit.py`
- **Depends on:** 2.1–2.7
- **Acceptance:** Tracks rolling 1h failure rate per adapter. Trip threshold 50% with min 4 attempts. On trip → halt that source for 60 min and WhatsApp critical.
- **Verify:** `uv run pytest agents/tests/test_circuit.py -v`
- **Refs:** arch.D Phase 5 step 3

---

### - [ ] Task 5.4 — Cookie / session healthcheck cron
- **Files:** `agents/tools/session_health.py`, `infra/com.career-ops.healthcheck.plist`, `agents/tests/test_session_health.py`
- **Depends on:** 2.6
- **Acceptance:** Every 6h, opens persistent context for each logged-in site, checks for login redirect. If session expired → WhatsApp prompt user to re-login before next scheduled apply.
- **Verify:** `uv run pytest agents/tests/test_session_health.py -v`
- **Refs:** arch.D Phase 5 step 4

---

### - [ ] Task 5.5 — Go TUI observability extensions
- **Files:** `dashboard/internal/views/observability.go`, `dashboard/internal/data/audit.go`, screenshots in `docs/`
- **Depends on:** 0.7
- **Acceptance:** New TUI tab: "Ops". Shows today's apps (count + status), $ spent on Claude + CAPTCHA, success rate per ATS family, current circuit state, pending approvals. Reads from `db/careerops.db` directly.
- **Verify:** Manual — launch `./dashboard/career-dashboard`, switch to Ops tab.
- **Refs:** arch.D Phase 5 step 5

---

## 🧱 Decision Log

| Date | Decision | Rationale | Reverts |
|---|---|---|---|
| 2026-05-12 | Python 3.12 (exact), `uv` only | 3.13 has scattered package compatibility issues; `uv` replaces pip/poetry/pipenv for speed and lockfile determinism | Revisit at 3.13.5+ when ecosystem catches up |
| 2026-05-12 | LangGraph 0.4+ over CrewAI/AutoGen | Best HITL semantics with `interrupt()` + `SqliteSaver` checkpointing required for pause-at-submit | — |
| 2026-05-12 | Playwright primary, Computer Use fallback | 92% vs 78% reliability; cost; deterministic on known ATS templates | — |
| 2026-05-12 | macOS Keychain default, 1Password CLI opt-in | Zero-license, OS-encrypted, unattended-friendly | — |
| 2026-05-12 | WhatsApp Cloud API (Meta direct) over Twilio + whatsapp-web.js | Free at our volume; whatsapp-web.js is unofficial and risks the user's personal account | — |
| 2026-05-12 | Markdown files remain source of truth; SQLite is operational mirror | Honors existing `DATA_CONTRACT.md`; preserves user-edit primacy | — |
| 2026-05-12 | No proxies, no fake accounts, no parallel sessions in Phase 1–4 | Conservative ToS posture; one human, one identity | Revisit only if home IP blocks repeatedly |
| 2026-05-12 | Repo lives at `~/code/career-ops` by convention | Standard macOS dev path; matches `direnv` / `nix develop` ergonomics | User can override at clone time |
| 2026-05-15 | Greenfield scaffold in `akulasaivineeth/Career-ops-autonomus` | Upstream `santifer/career-ops` Node/Go tree not vendored yet; `npm run doctor` checks repo layout until merge | Track in Decision Log until submodule or port |
| 2026-05-15 | Feature branch `cursor/foundations-scaffold-6b71` | Cloud agent policy requires `cursor/*-6b71` naming instead of `feat/autonomous-applier` from Task −1.1 | Parallel naming OK for automation |
| 2026-05-15 | `pysqlcipher3` / `sqlite-vec` as optional extras | Keeps default `uv sync` portable on CI without libsqlcipher headers; enable `[crypto]` when host ready (BUILD Task 5.1) | Revisit before encrypting DB |
| 2026-05-15 | `langgraph-checkpoint-sqlite` added for `SqliteSaver` | Upstream docs referenced `langgraph.checkpoint.sqlite`; package now ships as extra dependency (LangGraph 1.2+) | Keep version aligned with `langgraph` releases |

> **Add new entries** when you make any architectural choice that differs from the architecture doc or this plan.

---

## 🚧 Blockers

*None.* If you hit a blocker, append a row with: date, task ID, what failed (error + stack), what you tried, what is needed to unblock.

| Date | Task | Issue | Tried | Needs |
|---|---|---|---|---|
|  |  |  |  |  |

---

## ✅ Completed Milestones

- [ ] Phase −1 complete — cold start done, all toolchains green
- [ ] Phase 0 complete — Python scaffold, secrets vault, Gmail OAuth, bridge `/health`
- [ ] Phase 1 complete — first HITL-gated Greenhouse submission
- [ ] Phase 2 complete — all 5 source families operational
- [ ] Phase 3 complete — 20+ apps/day sustained for 5 days
- [ ] Phase 4 complete — autonomy level 2 stable for 7 days
- [ ] Phase 5 complete — hardened, encrypted, observable

---

## 📎 Appendix — Quick reference

**Daily commands during build:**

```bash
cd ~/code/career-ops
direnv allow .                       # one-time per shell session if .envrc changed
nix develop                          # enter dev shell (or auto via direnv)
uv sync                              # sync python deps
uv run python -m bridge              # start bridge server
ollama serve                         # start local LLM (separate terminal)
ollama pull qwen3:8b nomic-embed-text phi:3.8b   # one-time
uv run pytest -v                     # run python tests
npm run doctor                       # existing repo healthcheck
./dashboard/career-dashboard         # existing TUI
claude /apply <jd_id>                # dispatch an apply (Phase 1+)
```

**Status one-liner:**
```bash
echo "$(grep -c '^- \[x\]' BUILD.md) / $(grep -c '^- \[' BUILD.md) tasks complete"
```

**Key file locations:**
- Logs: `audit/{run_id}/`
- PDFs: `output/{run_id}.pdf`
- Reports: `reports/{NNN}-{slug}-{date}.md`
- DB: `db/careerops.db` (SQLCipher-encrypted from Phase 5)
- Browser contexts: `~/Library/Application Support/career-ops/browser/{site}/`
- Gmail OAuth client: `~/.career-ops/gmail-credentials.json` (NEVER in repo)
- Secrets: macOS Keychain, service prefix `careerops.*`

**Hard guardrails (never relax without user explicit say-so):**
1. No final-submit click without `request_human_approval` returning `"approved"`.
2. No account creation without approval.
3. No 2FA solve without either Gmail-extracted code OR user approval.
4. No LinkedIn profile scraping. Easy Apply only.
5. No fake accounts. No proxy networks.
6. No commits of `audit/`, `output/`, `db/careerops.db*`, browser context dirs, `.env`.
7. No mark-task-complete without verify passing.
8. No `git push` without user say-so.
9. No `sudo`, no destructive shell commands, no global package installs.
10. No proceeding without an explicit "go" before each task.

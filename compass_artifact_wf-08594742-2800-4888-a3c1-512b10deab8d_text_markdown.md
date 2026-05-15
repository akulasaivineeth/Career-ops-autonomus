# Architecture Document — Autonomous Multi-Agent Job Application OS
## Extending `santifer/career-ops` for macOS Apple Silicon

> **Scope.** A build-ready blueprint for converting the existing `santifer/career-ops` repository — today a Claude-Code-driven, human-in-the-loop evaluation pipeline — into a fully autonomous, multi-agent Job Application OS that runs locally on Apple Silicon, applies to 20–50 jobs per day across LinkedIn Easy Apply, Greenhouse/Lever/Ashby, Workday/Taleo, Indeed/Glassdoor/Wellfound, and arbitrary company career pages, with conservative HITL gates that relax over time.

---

## A. Current Repo Analysis (`santifer/career-ops` @ main, v1.7.0 / May 2026)

### What's there

The repo is a **Claude-Code-first, Node.js + Go monorepo** rather than a Python agent framework. Composition:

| Layer | Implementation |
|---|---|
| **Agent runtime** | Claude Code "skills" + slash commands. Multi-CLI shims for OpenCode, Gemini CLI, Codex, Qwen via `.agents/skills/`, `.claude/skills/`, `.qwen/skills/`, `.gemini/commands/*.toml`. Canonical agent instructions live in `AGENTS.md` and `CLAUDE.md` (211 lines). |
| **Skill modes** | 14 markdown "modes" in `modes/*.md`: `_shared.md` (global scoring + tools), `_profile.md` (user customization), `oferta.md` (single eval), `pdf.md`, `scan.md`, `batch.md`, plus `apply`, `pipeline`, `contacto`, `deep`, `training`, `project`. |
| **Dashboard** | **Go TUI** (Bubble Tea + Lipgloss, Catppuccin Mocha theme) in `dashboard/`. NOT Next.js/Streamlit/Flask. Built with `go build -o career-dashboard`. |
| **Data store** | **Plain files, not SQLite/Postgres.** `data/applications.md` (markdown table tracker), `data/pipeline.md` (URL inbox), `data/scan-history.tsv` (dedup), `data/follow-ups.md`, `reports/*.md` (eval reports formatted `{###}-{company-slug}-{YYYY-MM-DD}.md`), `output/*.pdf`. |
| **ATS scoring** | README and modes describe an **A–F evaluation rolled into a 1–5 scale** across "10 weighted dimensions" and a "6-Block Evaluation" (role summary, CV match, level strategy, comp research, personalization, interview prep STAR+R). Hard cutoff: **don't apply below 4.0/5**. Logic lives in `modes/_shared.md` and `modes/oferta.md`. |
| **Browser automation** | **Playwright (Chromium) in Node.js** used narrowly for: (1) HTML→PDF rendering in `generate-pdf.mjs`; (2) portal scanning in `scan.mjs` against Greenhouse/Lever/Ashby/Wellfound/Workable + WebSearch fallback. No login flows, no form submission, no Workday or LinkedIn coverage. |
| **CV generation** | `templates/cv-template.html` → Playwright/Puppeteer → PDF, Space Grotesk + DM Sans in `fonts/`. Plus `generate-latex.mjs` LaTeX track. |
| **Pipeline utilities** | `analyze-patterns.mjs`, `check-liveness.mjs`, `liveness-core.mjs`, `cv-sync-check.mjs`, `dedup-tracker.mjs`, `doctor.mjs`, `followup-cadence.mjs`, `merge-tracker.mjs`, `normalize-statuses.mjs`, `verify-pipeline.mjs`, `update-system.mjs`, `test-all.mjs` — `.mjs` Node scripts run from project root. |
| **Batch processing** | `batch/batch-runner.sh` orchestrates parallel `claude -p` workers using `batch/batch-prompt.md`. This is the closest thing to an "agent orchestrator" today — shell fan-out, not LangGraph/CrewAI. |
| **Configuration** | `config/profile.yml` (identity, targets, comp), `portals.yml` (45+ companies + 19 query templates), `templates/states.yml` (canonical statuses). |
| **Reproducibility** | `flake.nix` + `flake.lock`, `.envrc`, `renovate.json`, `release-please-config.json`. |
| **HITL today** | **One hard rule, repeated in `AGENTS.md`, `CLAUDE.md`, `LEGAL_DISCLAIMER.md`, README:** *"The system never submits an application — you always have the final call."* No `apply()` worker touches submit buttons. |

### What this means for the extension

- The repo is a **filter and tailor pipeline**, not an applier. We must **add the entire applier sub-system** without breaking the existing eval/PDF/tracker contract.
- `data/applications.md` is the markdown source of truth. Per `DATA_CONTRACT.md` it is "user layer (NEVER auto-updated)" — we must extend it (or shadow with SQLite for agent state) without overwriting user edits.
- The repo has no Python. The new applier sub-system will be a **parallel Python service** that reads/writes the same markdown/TSV artifacts and exposes a local FastAPI control plane the existing Go TUI and Claude Code skills can call.
- The existing `modes/apply.md` is described in the README as "fill application forms with AI" — currently a Claude Code skill that defers all submission to the user. It is the natural extension point: we rewrite it as a **dispatcher** that POSTs to the Python orchestrator.

### Files to **extend** (additive, contract-preserving)

| File | Change |
|---|---|
| `data/applications.md` | Add columns: `apply_status`, `apply_run_id`, `track` (DA/MLE/DE), `gate_log` ref, `screenshot_dir`. |
| `templates/states.yml` | Add canonical statuses: `apply_queued`, `apply_in_progress`, `awaiting_2fa`, `awaiting_approval`, `submitted`, `apply_failed`. |
| `modes/apply.md` | Convert from "fill in browser, user submits" to a dispatcher mode that hands off to the Python orchestrator over local socket. |
| `modes/_shared.md` | Add ATS-track router (DA/MLE/DE) and the extended scoring matrix (keyword + semantic + experience-fit). |
| `CLAUDE.md` | Document the autonomy ladder + HITL gates. |
| `LEGAL_DISCLAIMER.md` | Update for autonomous-mode warnings, ToS posture. |
| `config/profile.yml` | Add `tracks:` block (DA/MLE/DE bullet pools), `autonomy_level`, `whatsapp_number`, `gmail_account`, `proxy_pool`. |
| `flake.nix` | Add Python 3.12, `uv`, `playwright-python`, `ollama`. |

### New top-level modules to **create**

```
career-ops/
├── agents/                     # NEW — Python agent stack
│   ├── orchestrator/           # LangGraph state machine
│   ├── workers/                # scanner, scorer, tailor, applier, verifier, hitl
│   ├── tools/                  # gmail, keychain, captcha, whatsapp, browser_harness
│   ├── adapters/               # ats_greenhouse, ats_lever, ats_ashby, ats_workday,
│   │                           #   ats_linkedin, ats_indeed, ats_generic
│   ├── prompts/                # system prompts (one .md per agent)
│   └── tests/
├── db/                         # NEW — SQLite operational store (alongside markdown)
│   └── careerops.db
├── bridge/                     # NEW — local FastAPI control plane
├── audit/                      # NEW — per-run screenshots, DOM dumps, action diffs
├── cv/                         # NEW — per-track master CVs (da.md, mle.md, de.md)
└── docs/AUTONOMY.md            # NEW — HITL ladder
```

---

## B. Recommended Architecture

### B.1 High-level diagram

```
                           ┌──────────────────────────────────────────────┐
                           │  USER (macOS Apple Silicon)                  │
                           │  ── Claude Code CLI                          │
                           │  ── Go TUI dashboard (existing)              │
                           │  ── WhatsApp (HITL channel, mobile or web)   │
                           └───────────────┬──────────────────────────────┘
                                           │ local sockets / FastAPI
                                           ▼
   ┌──────────────────────────────────────────────────────────────────────────┐
   │   ORCHESTRATOR  (LangGraph 0.4 StateGraph + SqliteSaver checkpointer)    │
   │                                                                          │
   │   nodes:  scan → score → route_track → tailor → review_pdf →             │
   │           apply → verify → followup                                      │
   │   gates:  interrupt() before submit, account_creation, 2FA, captcha,     │
   │           anomaly (free-text custom Qs)                                  │
   └─────┬───────────┬──────────┬───────────┬───────────┬──────────┬──────────┘
         │           │          │           │           │          │
         ▼           ▼          ▼           ▼           ▼          ▼
   ┌─────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐ ┌───────┐ ┌──────────┐
   │SCANNER  │ │ SCORER   │ │TAILOR  │ │APPLIER  │ │VERIFY │ │HITL-     │
   │(Playwr.)│ │(Claude + │ │(Claude │ │(Playwr. │ │(Gmail │ │BRIDGE    │
   │+ Greenh.│ │ local LLM│ │+ track │ │+ Computer│ │+ DOM  │ │(WhatsApp │
   │ API +   │ │ for keyw │ │ chooser│ │ Use     │ │ diff) │ │ Cloud +  │
   │ Web)    │ │ extract) │ │ DA/MLE │ │ fallback│ │       │ │ approval │
   └─────────┘ └──────────┘ │ /DE)   │ │)        │ └───────┘ │ FSM)     │
                            └────────┘ └────┬────┘           └────┬─────┘
                                            │                     │
                                            │  per-site adapters  │
                                            ▼                     │
                  ┌──────────────────────────────────────┐         │
                  │ adapters/ ats_greenhouse, ats_lever, │         │
                  │ ats_ashby, ats_workday, ats_linkedin,│         │
                  │ ats_indeed, ats_generic              │         │
                  └──────────────────────────────────────┘         │
                                            │                     │
                  ┌─────────────────────────┴─────────────┐        │
                  ▼                                       ▼        ▼
            ┌──────────┐   ┌──────────┐   ┌──────────┐  ┌───────────────┐
            │ Keychain │   │ Gmail API│   │ CapSolver│  │  Audit log    │
            │ (keyring)│   │ (OAuth2) │   │ /2Captcha│  │  (SQLite +    │
            │ creds    │   │ 2FA mail │   │ CAPTCHA  │  │  screenshots) │
            └──────────┘   └──────────┘   └──────────┘  └───────────────┘
                                            │
                                            ▼
                                     ┌─────────────────────┐
                                     │ Ollama 0.19+ (MLX)  │
                                     │ Qwen3-8B / Qwen3.6  │
                                     │ Phi-4 / nomic-embed │
                                     └─────────────────────┘
```

### B.2 Agent roles

| Agent | Responsibility | LLM | Key tools |
|---|---|---|---|
| **Orchestrator** | LangGraph state machine. Routes JDs through scan→score→tailor→apply→verify. Owns checkpointing and HITL interrupts. | None directly (logic node) | `SqliteSaver`, `interrupt()` |
| **Scanner** | Pull new listings from Greenhouse JSON, Lever JSON, Ashby GraphQL, LinkedIn public job search (logged-out, JDs only), Indeed RSS, company-page Playwright crawl. Dedup against `scan-history.tsv`. | Local (Qwen3-8B) for JD parsing | `playwright`, `httpx`, `ats_*` adapters |
| **Scorer** | Compute 1–5 A–F score per existing weights, plus semantic similarity score against each track's CV. Decide track: DA / MLE / DE. | Claude Sonnet 4.5 for reasoning; Qwen3-8B for keyword extraction; `nomic-embed-text` for cosine | embedding store (SQLite + sqlite-vec), JD parser |
| **Tailor** | Rewrite resume bullets per track + JD keywords. Generate cover letter with company research. Emit HTML → PDF via existing `generate-pdf.mjs`. | Claude Sonnet 4.5 (cover letter + bullets), local for keyword density check | `generate-pdf.mjs`, web search |
| **Applier** | Drive browser. Detect ATS family. Playwright DOM for known templates; Anthropic Computer Use fallback for unknown forms. Fill fields. **Stop at submit / account-creation / 2FA gates.** | Claude Sonnet 4.5 (Computer Use); Playwright deterministic | `playwright`, `computer_use_20250124`, CAPTCHA, Keychain |
| **Verifier** | Confirm submission via post-submit DOM markers, confirmation email in Gmail within 10 min. Update `applications.md`. | Local Phi-4 for email classifier | Gmail API, Playwright |
| **HITL-Bridge** | Send WhatsApp messages with screenshot + summary + Approve/Reject. Maintain pending-approval FSM with 30-min timeout → 2h escalation. | None | WhatsApp Cloud API webhook, FastAPI |

### B.3 Data flow (per-application lifecycle)

```
1. SCANNER discovers JD → writes row in data/pipeline.md + jds/{id}.txt
2. ORCHESTRATOR.checkpoint("scan_complete")
3. SCORER reads JD + cv/{da,mle,de}.md → report.md + track decision
4. ORCHESTRATOR.checkpoint("scored")
5. If score < 4.0 OR kill_signal → status = "rejected_auto", exit
6. TAILOR produces tailored cv.html + cover_letter.md → generate-pdf.mjs
7. INTERRUPT[review_pdf]   (auto-pass when autonomy_level >= 2 and score >= 4.3)
   → WhatsApp: "JD #042 — Acme MLE — score 4.6 — PDF ready. Approve?"
8. APPLIER opens portal. Detects ATS family. Drives form fields from profile.yml
9. INTERRUPT[account_creation] if portal asks to register
10. INTERRUPT[twofa] if 2FA challenge appears (after Gmail polling fails)
11. INTERRUPT[final_submit] → WhatsApp with screenshot of final page
12. User taps Approve → Applier clicks submit
13. VERIFIER polls Gmail up to 10 min for confirmation; screenshots success page
14. ORCHESTRATOR writes applications.md row: status=submitted, run_id, evidence dir
```

### B.4 State management

- **LangGraph `StateGraph`** with a typed `TypedDict` carrying `jd_id`, `jd_url`, `jd_text`, `track`, `score`, `report_path`, `pdf_path`, `cover_path`, `apply_run_id`, `browser_context_path`, `gate_pending`, `gate_kind`, `last_screenshot`, `attempts`, `errors[]`, `autonomy_level`.
- **`SqliteSaver` checkpointer** at `db/careerops.db` — every state transition is durable. Crash recovery resumes from last checkpoint. This is LangGraph's documented HITL pattern (`interrupt()` + checkpointer) and the single biggest reason it beats CrewAI here (2026 industry consensus — LangGraph v0.4 in April 2026 explicitly added improved state persistence and HITL checkpoints).
- **Time-travel debugging:** LangGraph supports rolling back to any prior state — used for "redo the cover letter."

### B.5 Error handling

| Failure | Strategy |
|---|---|
| Browser navigation timeout | Retry ×3 exponential backoff. Screenshot. After 3 → escalate to Computer Use fallback. |
| ATS template parse fail | Fall back from deterministic Playwright adapter to Computer Use vision. Log `adapter_unknown=true`. |
| CAPTCHA | CapSolver (AI, ~$0.80/1K reCAPTCHA v2, ~$1.20/1K Turnstile). On 2nd consecutive failure → WhatsApp HITL escalation. |
| 2FA email | Poll Gmail API for matching code (regex near "code/verify/PIN" keywords) up to 120 s. If absent → WhatsApp ask user. |
| SMS 2FA | Always WhatsApp ask user. Never integrate Twilio inbound SMS — too much overhead for 20–50/day. |
| Rate limit / soft block | Pause that adapter 60 min; mark cookie jar suspect; rotate proxy if configured. |
| Hard ban signal (e.g., LinkedIn "restricted") | Halt that source globally. WhatsApp critical alert. No retries without human ack. |

### B.6 Security model (overview — full §E)

- All API keys & site passwords in **macOS Keychain** via Python `keyring` (default backend `keyring.backends.macOS.Keyring`). 1Password CLI (`op`) supported as secondary backend.
- Gmail OAuth refresh token sealed in Keychain with service name `careerops.gmail`.
- Per-site browser contexts at `~/Library/Application Support/career-ops/browser/{site}/` with `0700` perms.
- SQLite encrypted at rest via SQLCipher (`pysqlcipher3`).
- Every action emits audit record: `(ts, run_id, agent, tool, args_hash, dom_diff, screenshot_path)`. Screenshots auto-redact fields tagged `sensitive` in `modes/_shared.md`.

---

## C. Tech Stack Recommendation (with justification)

| Concern | Choice | Why (2026 community consensus + your constraints) |
|---|---|---|
| **Agent framework** | **LangGraph 0.4+ (April 2026)** | Best HITL via `interrupt()` + persistent `SqliteSaver`; deterministic control flow required for an applier that must pause precisely at submit/account/2FA boundaries; LangSmith trace observability is critical for an autonomous bot; converged 2026 verdict from PE Collective, Markaicode, 3Pillar, Pratik Pathak, Gurusup. **CrewAI** rejected: faster to prototype but delegation chains are "fragile in long-running unsupervised tasks" and HITL is "limited" requiring custom wrappers. **AutoGen/AG2** rejected: optimized for conversational debate; Microsoft has shifted strategic focus to Microsoft Agent Framework and major new feature development has slowed. **Pure Claude Code sub-agents** rejected: great for dev ergonomics, no durable checkpointing across hours/days. |
| **Where Claude Code fits** | Front-end + skill modes (existing) | We keep `claude` CLI as the user-facing co-pilot calling into the LangGraph orchestrator over a local MCP server. Preserves the repo's "Claude reads same files it uses" ethos. |
| **Browser layer — primary** | **Playwright (Python)** with `playwright-stealth` v2.x | Highest reliability on common tasks (~92% in DigitalApplied's 2026 benchmark vs. 78% for Computer Use). DOM access is required for Workday's multi-page state. Active maintenance, modern context-manager API (v2.0.2 April 2026). |
| **Browser layer — fallback** | **Anthropic Computer Use** (Claude Sonnet 4.5 `computer_use_20250124`) | For unknown ATS templates, canvas-driven anti-bot screens, and forms where DOM is intentionally obscured. ~78% reliability but unlocks workloads DOM can't reach. Integrated into Claude Code in Q1 2026. |
| **Browser DX wrapper (optional)** | **Stagehand 3** (Browserbase) for `act/extract/observe` primitives — only where useful | v3 (2026) dropped Playwright dep, went CDP-native, self-healing + caching reduces LLM cost. We will NOT use Browserbase managed runtime — everything runs locally per spec. |
| **Other 2025–2026 entrants considered** | **Browser-use** (50K+ ⭐ Python lib, full LLM-driven agent loop) — rejected as primary: re-reasons every step → too expensive at 20–50 apps/day; useful as ad-hoc tool. **Skyvern** — vision-first form filler aimed at exactly this use case but heavier than we need locally. **Playwright MCP** — token-cheap accessibility-tree server, ~4× fewer tokens than screenshot mode; we use it via Claude Code for dev/debug. **Camoufox** (Firefox source-patched, 0% headless detection but unstable beta) — keep as Plan B if Chrome+stealth gets blocked. **Patchright** — Chromium fork patching at C++ level; alternative if `playwright-stealth` JS-level patches become insufficient. **agent-browser / Vercel** — token-efficient but heavy wall-clock latency, not worth swapping in. **OpenAI CUA** — cloud-only, OpenAI-locked, contradicts your local-first preference. |
| **Stealth posture** | `playwright-stealth>=2.0.2` (Python, actively maintained) + headed Chromium (channel="chrome") + persistent context per site + 800–2400 ms human-like delays + macOS-native UA. **No residential proxies in phase 1.** Add Bright Data/Smartproxy only if LinkedIn/Workday start blocking from home IP. | Stealth plugins only address fingerprint signals — TLS, IP rep, behavioral analysis are unsolved by JS-level plugins. For 20–50/day from one residential home IP at human cadence, you stay below most thresholds. |
| **LLM split — heavy reasoning** | **Claude Sonnet 4.5** | Cover letters, complex form reasoning, Computer Use fallback, edge-case handling. |
| **LLM split — cheap & frequent** | **Ollama 0.19+ with MLX backend** on Apple Silicon | JD keyword extraction, resume bullet rephrasing draft, confirmation-email classification, dedup hashing. Ollama 0.19 (March 2026) ships MLX-native backend with 32 GB+ unified memory — ~15–30% faster than llama.cpp; close to MLX-LM speeds with Ollama's ergonomics. |
| **Local models** | **Default workhorse:** `qwen3:8b` (5.2 GB, Q4_K_M; ~45 tok/s on M3/M4 16 GB). **Heavy reasoning:** `qwen3.6:35b-a3b` MLX 4-bit (~19.5 GB; needs 32–48 GB Mac). **Embeddings:** `nomic-embed-text` (300 MB). **Classifier:** `phi:3.8b` or `gemma3:4b`. | Qwen3-8B is the 2026 consensus "16–24 GB Mac" sweet spot; Qwen3.6-35B-A3B MoE is the 32 GB+ pick (3 B active per token → fast). |
| **Local LLM runtime** | **Ollama 0.19+** primary; **LM Studio** for interactive dev; **MLX-LM** only when you want absolute fastest path for one model | Ollama is easiest path; closes speed gap with MLX on 32 GB+ Macs starting 0.19. |
| **Secrets vault** | **macOS Keychain via Python `keyring` ≥25.7** as default. Optional `1Password CLI (op)` backend via `onepassword-keyring`. | Best-practice for unattended local agents on macOS: zero extra license, idiomatic, OS-encrypted, no Docker friction. **Caveat:** by default any Python process the user runs can read entries — same as `security` CLI. Mitigation: open Keychain Access.app → Access Control on each `careerops.*` item → remove broad `python3` allow, "Always Allow" only the signed career-ops binary (this addresses the `jaraco/keyring` #457 concern). **Bitwarden CLI (`bw`)** supported but adds an unlock step that hurts unattended overnight runs. **Recommendation: Keychain default, `op` opt-in via `CAREEROPS_VAULT=op`.** |
| **CAPTCHA** | **CapSolver** primary, **2Captcha** fallback. Budget $5–10/month is comfortable at 20–50/day. | CapSolver is AI-only (3–9 s reCAPTCHA v2, ~$0.80/1K; ~$1.20/1K Turnstile, $6 min deposit). 2Captcha is human-backed (slower, ~$2.99/1K) but supports 30+ CAPTCHA types — best fallback for Arkose/FunCaptcha. Both have Playwright SDKs. Worst-case math: 50 apps × ~5% with CAPTCHA × $0.0015 ≈ $0.15/day. NopeCHA and Anti-Captcha considered but offer no advantage. |
| **WhatsApp HITL** | **WhatsApp Cloud API (Meta direct)** with self-hosted FastAPI webhook + Cloudflare Tunnel | Free at our volume — Meta's first 1,000 service conversations/month are free; we'll be well under 250. No Twilio per-message platform fee (~$0.005/msg) and no BSP layer. **whatsapp-web.js** is rejected: per its own README it is unofficial and "WhatsApp does not allow bots or unofficial clients on their platform … this shouldn't be considered totally safe" — unacceptable risk for the personal number you actually use. Twilio is acceptable Plan B if Meta verification is painful. |
| **DB** | Existing markdown/TSV **kept** as user-facing truth + **new SQLite (SQLCipher-encrypted)** at `db/careerops.db` for agent state, LangGraph checkpoints, audit log, embeddings. A reconciler syncs SQLite → `applications.md` after every state transition. | Honors `DATA_CONTRACT.md` (user files never auto-overwritten beyond append + status field); gives LangGraph durable checkpoints. |
| **Local control plane** | FastAPI on `127.0.0.1:8765` | Go TUI + Claude Code skills call `POST /run`, `GET /state/{run_id}`, `POST /approve/{run_id}`. |

### C.1 Per-site browser-automation posture

| Site family | Primary approach | Stealth notes |
|---|---|---|
| **LinkedIn Easy Apply** (high anti-bot) | Playwright + `playwright-stealth` driving a **manually-saved logged-in session** (storage state), Easy Apply iframe (`data-test-modal`) only. No profile scraping, no fake accounts. Caps: ≤8/hr, ≤25/day. | Real Chrome channel; gaussian 1.5–3 s field delays; no parallel sessions; halt globally on any "restricted" message. |
| **Workday/Taleo** (heavy multi-page forms) | Playwright deterministic for stable field-family selectors (`[data-automation-id*='*']`) + Computer Use fallback for novel pages. Persistent context per company subdomain (each Workday tenant is its own URL). | Highest detection-mitigation budget: 1500–3500 ms inter-action; never parallel per tenant; on bot screen → Camoufox plan-B; per-tenant cookie health checks. |
| **Greenhouse / Lever / Ashby** (standardized) | Playwright deterministic only. Greenhouse `boards-api.greenhouse.io/v1/boards/{co}/jobs` for listings; Lever postings API; Ashby public GraphQL. Forms have stable IDs (`#first_name`, `#email`, `#resume`). | Minimal stealth needed; basic delays sufficient. Safest stack — fastest path to volume. |
| **Indeed / Glassdoor** (medium friction) | Playwright + stealth + CapSolver for Turnstile. Easy Apply only. | Lower cap (≤15/day Indeed). Plan for Turnstile (CapSolver Turnstile endpoint). |
| **Wellfound** | Like Greenhouse — permissive, standard. | Standard Playwright. |
| **Generic company pages** | Computer Use vision-first (DOM is heterogeneous). | Conservative — no retries on hard blocks; WhatsApp on confusion. |

**When to use DOM vs vision:** DOM-driven (Playwright + selectors) is 12–17 percentage points more reliable on common tasks (2026 benchmark). Use vision-driven (Computer Use) only when (a) the ATS is unknown and detection fails confidence, (b) the form uses canvas/SVG widgets, or (c) Playwright is blocked by anti-bot DOM shadowing.

---

## D. Phased Implementation Roadmap

### Phase 0 — Foundations (Week 1, no behavior change)

1. Add Python tooling to `flake.nix`: `python312`, `uv`, `playwright`, `ollama`.
2. New top-level dirs: `agents/`, `db/`, `bridge/`, `audit/`, `cv/`.
3. Create `pyproject.toml` with `uv` (deps: `langgraph>=0.4`, `langchain-anthropic`, `langchain-ollama`, `playwright>=1.49`, `playwright-stealth>=2.0.2`, `anthropic>=0.40`, `keyring>=25.7`, `google-api-python-client`, `google-auth-oauthlib`, `httpx`, `fastapi`, `uvicorn`, `pysqlcipher3`, `sqlite-vec`, `nanoid`, `structlog`).
4. `agents/tools/keychain.py` — Keychain wrapper (see §G.4).
5. `agents/tools/gmail.py` — OAuth2 + verification-code extractor (see §G.1).
6. `bridge/server.py` — empty FastAPI scaffold with `/health`.
7. `db/schema.sql` — SQLite schema (§D.6).
8. `docs/AUTONOMY.md` — explicit ladder doc.
9. Update `CLAUDE.md`, `LEGAL_DISCLAIMER.md` — autonomous mode is opt-in and starts at level 1.

**Exit criteria:** `uv run python -c "from agents.tools.keychain import get_secret"` works. `npm run doctor` passes. No tracker changes.

### Phase 1 — MVP: Single-Site Applier with Maximum HITL (Weeks 2–3)

Apply to **one** Greenhouse job end-to-end with HITL at PDF approval, account creation, 2FA, and final submit.

1. `agents/orchestrator/graph.py` — LangGraph skeleton (§G.3).
2. `agents/workers/scorer.py` — extends `modes/oferta.md` logic; outputs JSON with track decision.
3. `agents/workers/tailor.py` — calls existing `generate-pdf.mjs` via subprocess; writes `output/{run_id}.pdf`.
4. `agents/adapters/ats_greenhouse.py` — Playwright + stealth, deterministic selectors.
5. `agents/tools/whatsapp.py` — WhatsApp Cloud API webhook bridge (§G.2).
6. `agents/tools/browser_harness.py` — hybrid Playwright + Computer Use harness (§G.5).
7. `bridge/server.py` — `/run`, `/state/{id}`, `/approve/{id}`, `/reject/{id}`.
8. `modes/apply.md` — rewrite as dispatcher: "POST to `localhost:8765/run` with `{jd_id}`."
9. Update `data/applications.md` schema; migrator in `normalize-statuses.mjs`.

**Autonomy level: 1.** Every gate fires WhatsApp.

**Exit criteria:** apply to 3 real Greenhouse jobs end-to-end with HITL at every gate. Zero submissions without user approval.

### Phase 2 — Multi-Site Coverage (Weeks 4–6)

1. `agents/adapters/ats_lever.py` — Lever standard postings.
2. `agents/adapters/ats_ashby.py` — Ashby GraphQL + form template.
3. `agents/adapters/ats_workday.py` — multi-page wizard; Playwright + stealth for known field-families, Computer Use for rest; persistent context per company subdomain.
4. `agents/adapters/ats_indeed.py` — Easy Apply + Glassdoor + Wellfound.
5. `agents/adapters/ats_linkedin.py` — Easy Apply only; no profile scraping; pre-existing logged-in session via storage state.
6. `agents/adapters/ats_generic.py` — Computer Use vision fallback for arbitrary company pages.
7. Per-adapter unit tests with recorded HAR fixtures.
8. CAPTCHA integration `agents/tools/captcha.py` (CapSolver primary + 2Captcha fallback).

**Autonomy level still 1.**

**Exit criteria:** all 5 source families produce ≥1 successful HITL-gated submission.

### Phase 3 — Volume & Verifier (Weeks 7–8)

1. `agents/workers/scanner.py` — replaces parts of `scan.mjs`: Greenhouse/Lever JSON, Ashby GraphQL, LinkedIn public job search (logged-out, JDs only).
2. `agents/workers/verifier.py` — Gmail polling for confirmation emails + DOM post-submit assertions.
3. Scorer extension with `nomic-embed-text` embeddings in `sqlite-vec`; semantic similarity to per-track CV.
4. Three CV tracks in `cv/da.md`, `cv/mle.md`, `cv/de.md`. Tailor picks based on Scorer's track decision; user reviews tailored version pre-submit.
5. Daily run scheduler via `launchd` plist (macOS native).
6. Rate limiter: max 8 applications/hour/source, max 25/day/source, gaussian inter-arrival.

**Autonomy level 2** (PDF approval auto-passes if score ≥ 4.3 and track unchanged from last successful; submit still HITL).

**Exit criteria:** 20+ applications/day for 5 consecutive days; zero ban signals; zero unintended submissions.

### Phase 4 — Easing into Autonomy (Weeks 9–12)

Autonomy ladder in `config/profile.yml`:

```yaml
autonomy:
  level: 2          # 0=dry-run, 1=approve-everything, 2=approve-submit-only,
                    # 3=approve-anomalies-only, 4=full-auto
  rules:
    submit_gate: hitl              # hitl | auto_if_score_ge_4_5 | auto
    account_creation: hitl         # hitl | auto
    twofa: hitl                    # hitl | auto_gmail | hitl
    pdf_review: auto_if_track_stable
    captcha_after_3_fail: hitl
    new_site_first_time: hitl_always
```

1. Auto-pass submit when: score ≥ 4.5 AND ATS ∈ {Greenhouse, Lever, Ashby} AND form has zero free-text custom questions AND verifier dry-run passes.
2. Anomaly detector: classifies forms — non-standard questions (e.g. "Why this company?") force HITL even at high autonomy.
3. Weekly WhatsApp digest: apps sent, response rate, anomalies queued for Sunday batch review.

### Phase 5 — Hardening (Weeks 13+)

1. SQLCipher encryption at rest.
2. Screenshot redaction (regex + OCR-based SSN/salary detection).
3. Per-adapter circuit breakers.
4. Cookie/session healthchecks on cron — preemptively re-prompt user before LinkedIn session expires.
5. Cost/observability in Go TUI: tokens spent, $ on Claude, $ on CAPTCHA, success rate per ATS family.

### D.6 SQLite schema

```sql
CREATE TABLE runs (
  run_id TEXT PRIMARY KEY,
  jd_id TEXT NOT NULL,
  jd_url TEXT,
  track TEXT CHECK (track IN ('DA','MLE','DE')),
  score REAL,
  ats_family TEXT,
  status TEXT NOT NULL,
  autonomy_level INT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE checkpoints (
  thread_id TEXT, checkpoint_id TEXT, state BLOB,
  PRIMARY KEY (thread_id, checkpoint_id)
);
CREATE TABLE actions (
  id INTEGER PRIMARY KEY,
  run_id TEXT REFERENCES runs(run_id),
  ts TEXT NOT NULL, agent TEXT NOT NULL, tool TEXT NOT NULL,
  args_hash TEXT, dom_diff_path TEXT, screenshot_path TEXT, outcome TEXT
);
CREATE TABLE approvals (
  run_id TEXT, gate TEXT,
  sent_at TEXT, decided_at TEXT, decision TEXT,
  whatsapp_message_id TEXT,
  PRIMARY KEY (run_id, gate)
);
CREATE TABLE jd_embeddings (
  jd_id TEXT PRIMARY KEY, embedding BLOB    -- 768-d nomic-embed-text
);
```

---

## E. Security & Ethics

### E.1 ToS / legal posture per site (as of May 2026)

| Site | Posture | Practical guidance |
|---|---|---|
| **LinkedIn** | After *hiQ v. LinkedIn* (9th Cir. 2022, permanent injunction Dec 2022), scraping *public* data is not per se a CFAA violation, but **breach-of-contract claims survive**. LinkedIn has shown teeth in 2025–2026: enforcement against Apollo.io, Seamless.AI, Nubela/Proxycurl (2026 settlement). New theory emerging (Reddit v. Perplexity, pending) under DMCA §1201 for circumvention of rate-limit/anti-bot technical measures. | **Do not scrape profiles. Do not create fake accounts. Do not run proxy networks to multiply identities.** Easy Apply, from your real logged-in session, at human cadence, with stealth — is structurally similar to a power user with a browser extension. Document everything in the audit log. Caps: ≤8 Easy Apply/hr, ≤25/day. Halt on any "restricted" message. |
| **Workday** | No landmark case yet; aggressive anti-bot (DataDome-class). Enforcement mostly via account lock, not litigation. | Highest detection-mitigation budget: persistent context per tenant, 1500–3500 ms delays, Computer Use fallback when DOM is obscured; never parallel sessions per tenant. |
| **Greenhouse / Lever / Ashby** | Generally permissive — they expose JSON/GraphQL listings endpoints explicitly. Forms are user-submitted; bot detection minimal. | Safest stack. Prefer official APIs over scraping where possible. |
| **Indeed / Glassdoor** | Indeed bans automation explicitly; Glassdoor uses Cloudflare Turnstile. Moderate enforcement. | Easy Apply only. Lower per-day cap (≤15/day Indeed). |
| **Wellfound** | Smaller, mostly permissive. Standard form layout. | Treat like Greenhouse. |
| **Company career pages** | Each ToS individual. Most are silent on automation. | Conservative — Computer Use fallback; no retries on hard blocks. |

### E.2 Conservative-mode design principles

1. **One human, one identity.** No proxy rotation, no fake accounts, no parallel sessions per site. The audit story you can defend is: "I am a job seeker using an assistive tool to fill forms; every submission is for a job I personally evaluated."
2. **Human-in-the-loop preserved.** Per the repo's own `LEGAL_DISCLAIMER.md`: "Always review AI-generated content for accuracy before submitting." Default autonomy honors this until user explicitly relaxes it.
3. **No bulk scraping of user data.** Pull JD text only, never profiles, salaries, or contact lists.
4. **Rate limiting that mirrors a power user.** ≤25 Easy Apply/day on LinkedIn, ≤50/day total. Gaussian inter-arrival; pauses 22:00–08:00 local unless user opts in.
5. **Stop on signals.** "Restricted," "verify you're human" loops, sudden 429s → freeze the source globally and WhatsApp the user.
6. **Encrypted, redacted audit trail.** Every page screenshotted before & after; SSN/salary/DOB fields redacted at capture time.
7. **The user can disprove.** Subpoena-grade trail of "I, the human, approved this submission at this timestamp" lives in `approvals` table forever.

### E.3 Detection-mitigation strategies (per layer)

| Layer | Strategy |
|---|---|
| TLS fingerprint | Unsolved by JS-level stealth plugins. Mitigate by running Chromium with the user's actual installed Chrome via `channel="chrome"`, not bundled Chromium. Plan B: Camoufox (Firefox source-patched) or CloakBrowser (Chromium source-patched) — both ship Playwright-compatible APIs. |
| JS fingerprint | `playwright-stealth>=2.0.2` patches `navigator.webdriver`, plugins, WebGL noise, mime types. |
| Behavioral | Human-like delays (gaussian µ=1.2 s σ=0.4 s between fields), Bezier mouse curves, scroll patterns. |
| IP | **Phase 1: home IP only.** Phase 5: optional Bright Data residential proxy with sticky session if home IP gets throttled. |
| Cookies/session | Persistent context per site at `~/Library/Application Support/career-ops/browser/{site}/`. Storage state refreshed on every successful login. |
| Cadence | Max 8/hr/source, max 25/day/source, max 50/day total. Pause 22:00–08:00. |

### E.4 Approval gate state machine

```
[GATE_TRIGGERED]
   │ orchestrator emits interrupt(gate_kind)
   ▼
[PENDING] ─── HITL-Bridge sends WhatsApp: screenshot + summary + buttons
   │
   ├─ user replies "approve"/"yes" within 30 min ─► [APPROVED] ─► resume graph
   ├─ user replies "reject"/"no"/"skip"         ─► [REJECTED] ─► mark rejected, exit
   └─ timeout 30 min                            ─► [ESCALATED]
                                                    │ retry notification once
                                                    │ no reply in 2h → [AUTO_PAUSE]
                                                    ▼
                                          [AUTO_PAUSE] mark run paused;
                                                       resume only on explicit /resume
```

Stored in `approvals` table. LangGraph `interrupt()` pauses the state graph until `bridge.server.POST /approve/{run_id}` calls `graph.update_state(...)` + `graph.invoke(None, config)` to resume.

---

## F. Agent System Prompts & Tool Schemas

Canonical system prompts for each agent. Each is a LangGraph node calling Claude Sonnet 4.5 (or local Qwen3 for cheap tasks) with these prompts + the JSON-schema'd tools below.

### F.1 Orchestrator

Pure Python state-machine node (no LLM). Schema is the LangGraph `StateGraph` (see §G.3).

### F.2 Scanner

```
You are the Scanner agent in career-ops. Your job: find new job listings
the user has not yet evaluated, normalize them, add them to the pipeline.

INPUTS:
- portals.yml (45+ companies, query templates)
- data/scan-history.tsv (dedup hashes)
- user_tracks: ["DA", "MLE", "DE"]

RULES:
- Use legitimate public APIs first (Greenhouse boards-api, Lever postings,
  Ashby public GraphQL). Only fall back to Playwright when no API.
- Never log into any site to scan.
- Hash (company_slug, role_title, location) for dedup.
- For each new JD: download full text → write jds/{id}.txt and append to
  data/pipeline.md with status=queued.

DO NOT score, tailor, or apply. DO NOT pull more than 200 new JDs per run.
DO NOT re-scan a source that returned a 429 in the last hour.

OUTPUT (JSON):
{"new_jd_ids": [...], "skipped_duplicates": N, "sources_failed": [...]}
```

Tool schemas:

```json
[
  {"name":"http_get","description":"GET a URL, optional headers/params","input_schema":{
    "type":"object","required":["url"],"properties":{
      "url":{"type":"string"},"headers":{"type":"object"},"params":{"type":"object"}}}},
  {"name":"playwright_navigate","description":"Open a URL in a stealth context and return HTML","input_schema":{
    "type":"object","required":["url"],"properties":{"url":{"type":"string"},"wait_until":{"type":"string"}}}},
  {"name":"hash_dedup","description":"Return true if (company,role,location) already seen","input_schema":{
    "type":"object","required":["company","role","location"],"properties":{
      "company":{"type":"string"},"role":{"type":"string"},"location":{"type":"string"}}}},
  {"name":"write_pipeline_row","description":"Append a row to data/pipeline.md","input_schema":{
    "type":"object","required":["jd_id","url","title","company"],"properties":{
      "jd_id":{"type":"string"},"url":{"type":"string"},"title":{"type":"string"},
      "company":{"type":"string"},"location":{"type":"string"},"source":{"type":"string"}}}}
]
```

### F.3 Scorer

```
You are the Scorer agent. Score a single JD against the user's three CV
tracks (Data Analyst, ML Engineer, Data Engineer) using the existing
career-ops 1-5 A-F evaluation logic in modes/oferta.md PLUS a semantic
similarity score and experience-fit signal.

INPUTS:
- jd_text
- cv/da.md, cv/mle.md, cv/de.md (three tracks)
- config/profile.yml (comp targets, must-haves, deal-breakers)
- modes/_shared.md (10-dimension weights)

PROCESS:
1. Use qwen3_extract_jd to extract: title, level, location, remote_policy,
   stack[], requirements_must[], requirements_nice[], comp_range,
   years_required, sponsorship_offered.
2. For each track, compute three sub-scores (0..1):
   a) keyword_match  = |must_haves ∩ cv_skills| / |must_haves|
   b) semantic_sim   = cosine(nomic_embed(jd), nomic_embed(cv_track))
   c) experience_fit = clamp(user.years_in_track / jd.years_required, 0, 1)
3. Composite per-track score (0..1):
   composite = 0.40*keyword_match + 0.35*semantic_sim + 0.25*experience_fit
4. Pick the track with highest composite (ties → user's preferred track in profile).
5. Run the 10-dimension A-F evaluation against that track only:
   role_fit, comp, remote_policy, level_fit, growth, leadership_signal,
   tech_stack_match, company_quality, learning_value, geographic_fit.
6. Roll up to 1-5 score using existing weights in modes/_shared.md.

OUTPUT (JSON):
{
  "track": "MLE",
  "score": 4.4,
  "subscores": {"keyword_match":0.78,"semantic_sim":0.83,"experience_fit":0.90},
  "dimensions": {"role_fit":5,"comp":4,"remote":5, ...},
  "rationale": "...",
  "kill_signals": [],
  "tailor_keywords": ["LLM evaluation","RAG","Python","PyTorch"]
}

RULES:
- Below 4.0/5: status=rejected_auto, no PDF generation.
- 4.0–4.4: status=score_borderline, requires HITL even at autonomy_level=3.
- 4.5+: status=score_pass, proceeds to Tailor.
- ANY kill_signal: status=rejected_auto regardless of score.
```

Tool schemas:

```json
[
  {"name":"qwen3_extract_jd","description":"Local LLM extracts structured fields from JD text","input_schema":{
    "type":"object","required":["jd_text"],"properties":{"jd_text":{"type":"string"}}}},
  {"name":"embed_text","description":"Return nomic-embed-text 768-d vector","input_schema":{
    "type":"object","required":["text"],"properties":{"text":{"type":"string"}}}},
  {"name":"cosine_sim","input_schema":{
    "type":"object","required":["a","b"],"properties":{
      "a":{"type":"array","items":{"type":"number"}},
      "b":{"type":"array","items":{"type":"number"}}}}},
  {"name":"read_file","input_schema":{
    "type":"object","required":["path"],"properties":{"path":{"type":"string"}}}}
]
```

### F.4 Tailor

```
You are the Tailor agent. Produce a tailored CV PDF and cover letter for
a single JD on a single track.

INPUTS:
- jd_text, track ("DA"|"MLE"|"DE")
- cv/{track}.md (master CV)
- tailor_keywords (from Scorer)
- profile.yml (voice, do/don't lists)
- examples/ (good past tailored CVs as few-shot)

PROCESS:
1. Rewrite up to 8 resume bullets to maximize relevance, PRESERVING TRUTH.
   Never invent skills, companies, dates, or numbers.
2. Generate a 150–220 word cover letter with one paragraph of researched
   company-specific reasoning. Use web_search to pull 2–3 recent facts
   (funding, product launch, leadership change).
3. Hand the tailored markdown to generate-pdf.mjs via subprocess.
4. Write output/{run_id}.pdf and output/{run_id}-cover.md.
5. Emit a diff vs the master CV so the user can review in WhatsApp.

RULES:
- NEVER fabricate. If the JD asks for a skill not on the CV, do not add
  it. Lower the score instead and let the orchestrator decide.
- Same fonts (Space Grotesk + DM Sans), same ATS-friendly template.
- Use Claude Sonnet 4.5 for bullet rewriting (quality matters). Use Qwen3
  only for keyword-density verification post-hoc.

OUTPUT (JSON):
{"pdf_path":"...","cover_path":"...","diff_summary":"..."}
```

Tool schemas:

```json
[
  {"name":"claude_rewrite_bullets","input_schema":{
    "type":"object","required":["bullets","keywords","jd_text"],"properties":{
      "bullets":{"type":"array","items":{"type":"string"}},
      "keywords":{"type":"array","items":{"type":"string"}},
      "jd_text":{"type":"string"}}}},
  {"name":"web_search","input_schema":{
    "type":"object","required":["query"],"properties":{"query":{"type":"string"},"max":{"type":"integer"}}}},
  {"name":"subprocess_node","description":"Run a Node script and return stdout","input_schema":{
    "type":"object","required":["script","args"],"properties":{
      "script":{"type":"string"},"args":{"type":"array","items":{"type":"string"}}}}},
  {"name":"write_file","input_schema":{
    "type":"object","required":["path","content"],"properties":{
      "path":{"type":"string"},"content":{"type":"string"}}}}
]
```

### F.5 Applier

```
You are the Applier agent. Drive a real browser to submit one job
application. Three immutable rules:

RULE 1 — STOP AT GATES. Before clicking final SUBMIT, before creating any
new account, and before solving any 2FA challenge, you MUST call
request_human_approval(gate_kind, screenshot, summary) and wait for the
orchestrator to resume you.

RULE 2 — NO INVENTION. Every field you fill comes from config/profile.yml
or the tailored documents. If a required field is missing, raise
MissingFieldError and pause.

RULE 3 — ATS-FAMILY ADAPTER FIRST, COMPUTER USE FALLBACK. Detect ATS by
URL pattern + DOM markers. Use the deterministic adapter if confidence
> 0.8. Else fall back to vision-based Computer Use.

INPUTS:
- jd_url, run_id, track
- pdf_path, cover_path
- profile.yml (identity, work_auth, salary, etc.)
- browser_context_path (persistent cookies for this site)

PROCESS:
1. Open browser with persistent context for this site.
2. Navigate to jd_url. Detect ATS family.
3. Load adapter. Iterate over expected form fields, filling from profile.
4. Unknown fields: ask Claude (vision) what they are; fill if obvious,
   pause otherwise.
5. Upload pdf_path. Paste cover letter if a free-text "Why this role?"
   field exists.
6. Take screenshot. Call request_human_approval("final_submit", ...).
7. On approve: click Submit. Capture confirmation screenshot.
8. Hand off to Verifier.

ERROR HANDLING:
- CAPTCHA: try captcha_solve(); 2nd fail → request_human_approval("captcha").
- Account-creation prompt: ALWAYS request_human_approval("account_creation").
- 2FA: poll Gmail via gmail_get_verification_code() for 120 s; if absent →
  request_human_approval("twofa").
- Bot-detection / "restricted" page: stop, screenshot, raise HardBlockError,
  halt this source globally for 1 hour, WhatsApp critical.
```

Tool schemas:

```json
[
  {"name":"playwright_goto","input_schema":{
    "type":"object","required":["url"],"properties":{"url":{"type":"string"}}}},
  {"name":"playwright_fill","input_schema":{
    "type":"object","required":["selector","value"],"properties":{
      "selector":{"type":"string"},"value":{"type":"string"},"human":{"type":"boolean"}}}},
  {"name":"playwright_upload","input_schema":{
    "type":"object","required":["selector","path"],"properties":{
      "selector":{"type":"string"},"path":{"type":"string"}}}},
  {"name":"playwright_click","input_schema":{
    "type":"object","required":["selector"],"properties":{"selector":{"type":"string"}}}},
  {"name":"computer_use","description":"One step of vision-driven action","input_schema":{
    "type":"object","required":["instruction"],"properties":{"instruction":{"type":"string"}}}},
  {"name":"captcha_solve","input_schema":{
    "type":"object","required":["type","site_key","page_url"],"properties":{
      "type":{"type":"string","enum":["recaptcha_v2","recaptcha_v3","turnstile","hcaptcha"]},
      "site_key":{"type":"string"},"page_url":{"type":"string"}}}},
  {"name":"gmail_get_verification_code","input_schema":{
    "type":"object","required":["sender_domain"],"properties":{
      "sender_domain":{"type":"string"},"poll_seconds":{"type":"integer"}}}},
  {"name":"keychain_get","input_schema":{
    "type":"object","required":["name"],"properties":{"name":{"type":"string"},"account":{"type":"string"}}}},
  {"name":"take_screenshot","input_schema":{
    "type":"object","required":["label"],"properties":{"label":{"type":"string"},"redact":{"type":"boolean"}}}},
  {"name":"request_human_approval","input_schema":{
    "type":"object","required":["gate_kind","screenshot_path","summary"],"properties":{
      "gate_kind":{"type":"string","enum":["pdf_review","account_creation","twofa","final_submit","captcha","anomaly"]},
      "screenshot_path":{"type":"string"},"summary":{"type":"string"},
      "timeout_seconds":{"type":"integer"}}}}
]
```

### F.6 Verifier

```
You are the Verifier agent. Confirm a submitted application actually landed.

INPUTS: run_id, jd_url, company_slug, submitted_at

PROCESS:
1. Poll Gmail up to 10 min with q="from:({company_domain} OR
   noreply@greenhouse.io OR noreply@lever.co OR donotreply@ashbyhq.com OR
   noreply@myworkdayjobs.com) newer_than:1h". Classify each hit with
   phi4_classify_email as confirmation | rejection | newsletter.
2. Re-load jd_url. Check post-submit DOM markers: "Thanks for applying",
   "Application received", confirmation URL pattern.
3. Write evidence to audit/{run_id}/verifier/ (screenshots + .eml).
4. Update applications.md: status=submitted with evidence path.

OUTPUT: {"confirmed": true|false, "evidence": ["email_msg_id", "screenshot.png"]}
```

Tool schemas: `gmail_search`, `gmail_get_message`, `phi4_classify_email`, `playwright_navigate`, `take_screenshot`.

### F.7 HITL-Bridge

Not a prompted LLM — a Python service. Public function the orchestrator calls:

```python
def request_human_approval(
    run_id: str,
    gate_kind: Literal["pdf_review","account_creation","twofa",
                       "final_submit","captcha","anomaly"],
    screenshot_path: str,
    summary: str,                # <= 800 chars, plain text
    options: list[str] = ["approve","reject"],
    timeout_seconds: int = 1800,
) -> Literal["approved","rejected","timeout"]
```

---

## G. Next Steps / First-PR Starter Code

> Minimum-viable snippets. Production hardening (retries, logging, error envelopes, type checking) to be added in PR review.

### G.1 Gmail OAuth + verification-code extractor (`agents/tools/gmail.py`)

```python
"""Gmail tool: OAuth2 install flow, search, verification-code extraction."""
from __future__ import annotations
import base64, json, re, time
from pathlib import Path
from typing import Optional
import keyring
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scope minimization: gmail.readonly is enough for code extraction and
# confirmation-email detection. gmail.modify is added ONLY because we want
# to mark verification mails as read so we don't re-trigger on stale codes.
# We deliberately AVOID:
#   - https://mail.google.com/   (full access; restricted scope, security review)
#   - gmail.send / gmail.compose (we never send mail)
# Restricted scopes would trigger Google's annual third-party security
# assessment, which is overkill for a local single-user app.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

KEYRING_SERVICE = "careerops.gmail"
KEYRING_USER = "oauth_token_json"
CRED_FILE = Path.home() / ".career-ops" / "gmail-credentials.json"

VERIFICATION_RE = re.compile(
    r"(?:code|pin|verification|verify|otp|one[\- ]?time)\D{0,30}(\d{4,8})\b",
    re.IGNORECASE,
)

def _load_creds() -> Optional[Credentials]:
    token_json = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
    if token_json:
        return Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
    return None

def _save_creds(creds: Credentials) -> None:
    keyring.set_password(KEYRING_SERVICE, KEYRING_USER, creds.to_json())

def get_service():
    creds = _load_creds()
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CRED_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        _save_creds(creds)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)

def search(query: str, max_results: int = 10) -> list[dict]:
    svc = get_service()
    resp = svc.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    return resp.get("messages", [])

def get_body_text(msg_id: str) -> str:
    svc = get_service()
    msg = svc.users().messages().get(userId="me", id=msg_id, format="full").execute()
    def walk(payload):
        if payload.get("mimeType", "").startswith("text/"):
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
        for part in payload.get("parts", []) or []:
            t = walk(part)
            if t:
                return t
        return ""
    return walk(msg["payload"])

def mark_read(msg_id: str) -> None:
    svc = get_service()
    svc.users().messages().modify(userId="me", id=msg_id,
                                  body={"removeLabelIds": ["UNREAD"]}).execute()

def get_verification_code(
    sender_domain: str,
    *,
    poll_seconds: int = 120,
    interval: int = 5,
    newer_than: str = "10m",
) -> Optional[str]:
    """Poll Gmail for a verification code from a given sender domain."""
    deadline = time.time() + poll_seconds
    q = f"from:({sender_domain}) newer_than:{newer_than}"
    seen: set[str] = set()
    while time.time() < deadline:
        for m in search(q, max_results=5):
            if m["id"] in seen:
                continue
            seen.add(m["id"])
            body = get_body_text(m["id"])
            match = VERIFICATION_RE.search(body)
            if match:
                mark_read(m["id"])
                return match.group(1)
        time.sleep(interval)
    return None

if __name__ == "__main__":
    # One-time install: place client_secret.json at ~/.career-ops/gmail-credentials.json
    print(get_service().users().getProfile(userId="me").execute())
```

**Why Gmail API over IMAP (per your §4 question):**
- OAuth2 refresh tokens vs. app passwords (much safer at rest; revocable from a single dashboard).
- Structured queries (`from:`, `newer_than:`, `subject:`) make code extraction precise — IMAP requires fetching whole messages and filtering client-side.
- Free quota of 1 billion units/day is more than enough.
- Push (watch + Pub/Sub) is available if we want webhooks instead of polling later; IMAP IDLE works but is much more fragile.
- One scope upgrade path (sensitive scope review) if we ever need `gmail.send` for follow-ups.

**Setup:** Google Cloud Console → enable Gmail API → OAuth client ID (Desktop application) → download `client_secret.json` → save to `~/.career-ops/gmail-credentials.json` → first run pops browser for consent → refresh token sealed in Keychain.

### G.2 WhatsApp HITL bridge (`agents/tools/whatsapp.py` + `bridge/server.py`)

```python
# agents/tools/whatsapp.py — WhatsApp Cloud API client (Meta direct)
from __future__ import annotations
import os, httpx, keyring
from pathlib import Path

PHONE_NUMBER_ID = os.environ["WA_PHONE_NUMBER_ID"]
TO_NUMBER = os.environ["WA_USER_NUMBER"]          # e.g. +14155551234
GRAPH = "https://graph.facebook.com/v21.0"

def _token() -> str:
    return keyring.get_password("careerops.whatsapp", "access_token")

def send_text(text: str) -> str:
    r = httpx.post(
        f"{GRAPH}/{PHONE_NUMBER_ID}/messages",
        headers={"Authorization": f"Bearer {_token()}"},
        json={"messaging_product": "whatsapp", "to": TO_NUMBER,
              "type": "text", "text": {"body": text[:4096]}},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["messages"][0]["id"]

def send_image_with_caption(image_path: str, caption: str) -> str:
    with open(image_path, "rb") as f:
        media = httpx.post(
            f"{GRAPH}/{PHONE_NUMBER_ID}/media",
            headers={"Authorization": f"Bearer {_token()}"},
            data={"messaging_product": "whatsapp", "type": "image/png"},
            files={"file": (Path(image_path).name, f, "image/png")},
            timeout=60,
        )
        media.raise_for_status()
        media_id = media.json()["id"]
    r = httpx.post(
        f"{GRAPH}/{PHONE_NUMBER_ID}/messages",
        headers={"Authorization": f"Bearer {_token()}"},
        json={"messaging_product": "whatsapp", "to": TO_NUMBER,
              "type": "image", "image": {"id": media_id, "caption": caption[:1024]}},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["messages"][0]["id"]
```

```python
# bridge/server.py — FastAPI control plane + WhatsApp webhook
from __future__ import annotations
import asyncio, os, sqlite3, time
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from agents.tools.whatsapp import send_image_with_caption, send_text

DB = "db/careerops.db"
APPROVALS_WAITING: dict[str, asyncio.Future] = {}
VERIFY_TOKEN = os.environ["WA_WEBHOOK_VERIFY_TOKEN"]

app = FastAPI()

class ApprovalRequest(BaseModel):
    run_id: str
    gate: str
    screenshot_path: str
    summary: str
    timeout_seconds: int = 1800

@app.post("/internal/request_approval")
async def request_approval(req: ApprovalRequest):
    """Called by the orchestrator. Sends WhatsApp + awaits reply or timeout."""
    msg_id = send_image_with_caption(
        req.screenshot_path,
        f"🤖 career-ops gate: {req.gate}\nrun: {req.run_id}\n\n{req.summary}\n\nReply: APPROVE or REJECT",
    )
    _record_pending(req.run_id, req.gate, msg_id)
    loop = asyncio.get_event_loop()
    fut: asyncio.Future = loop.create_future()
    APPROVALS_WAITING[req.run_id] = fut
    try:
        decision = await asyncio.wait_for(fut, timeout=req.timeout_seconds)
        return {"decision": decision}
    except asyncio.TimeoutError:
        send_text(f"⏰ Timeout on run {req.run_id} ({req.gate}). Paused — reply RESUME or CANCEL.")
        return {"decision": "timeout"}
    finally:
        APPROVALS_WAITING.pop(req.run_id, None)

@app.get("/webhook/whatsapp")
async def verify(hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = ""):
    if hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(403)

@app.post("/webhook/whatsapp")
async def inbound(request: Request):
    body = await request.json()
    try:
        msg = body["entry"][0]["changes"][0]["value"]["messages"][0]
        text = msg.get("text", {}).get("body", "").strip().lower()
    except (KeyError, IndexError):
        return {"ok": True}
    if APPROVALS_WAITING:
        run_id = next(reversed(APPROVALS_WAITING))
        fut = APPROVALS_WAITING[run_id]
        if text in ("approve","yes","y","ok"):
            fut.set_result("approved");  _record_decision(run_id, "approved")
        elif text in ("reject","no","n","skip"):
            fut.set_result("rejected");  _record_decision(run_id, "rejected")
    return {"ok": True}

def _record_pending(run_id, gate, msg_id):
    with sqlite3.connect(DB) as c:
        c.execute("INSERT INTO approvals(run_id,gate,sent_at,whatsapp_message_id) VALUES(?,?,?,?)",
                  (run_id, gate, time.time(), msg_id))

def _record_decision(run_id, decision):
    with sqlite3.connect(DB) as c:
        c.execute("UPDATE approvals SET decided_at=?,decision=? WHERE run_id=?",
                  (time.time(), decision, run_id))
```

**Setup:** Meta for Developers → create Business app → add WhatsApp product → get `WA_PHONE_NUMBER_ID` + permanent access token → expose `http://localhost:8765/webhook/whatsapp` via Cloudflare Tunnel (`cloudflared tunnel`) → store token via `keyring set careerops.whatsapp access_token`.

### G.3 LangGraph orchestrator skeleton (`agents/orchestrator/graph.py`)

```python
"""career-ops orchestrator — LangGraph StateGraph with HITL interrupts."""
from __future__ import annotations
import httpx
from pathlib import Path
from typing import Literal, TypedDict
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END

from agents.workers.scorer import score_jd
from agents.workers.tailor import tailor_resume
from agents.workers.applier import drive_application
from agents.workers.verifier import verify_submission

class AppState(TypedDict):
    run_id: str
    jd_id: str
    jd_url: str
    jd_text: str
    track: str | None              # "DA" | "MLE" | "DE"
    score: float | None
    report_path: str | None
    pdf_path: str | None
    cover_path: str | None
    ats_family: str | None
    autonomy_level: int
    errors: list[str]
    gate_pending: str | None
    screenshot_path: str | None

def n_score(state: AppState) -> AppState:
    res = score_jd(state["jd_text"])
    return {**state, "track": res["track"], "score": res["score"],
            "report_path": res["report_path"]}

def r_after_score(state: AppState) -> Literal["tailor", "end"]:
    return "end" if state["score"] is None or state["score"] < 4.0 else "tailor"

def n_tailor(state: AppState) -> AppState:
    out = tailor_resume(state["jd_text"], state["track"], state["run_id"])
    return {**state, "pdf_path": out["pdf_path"], "cover_path": out["cover_path"]}

def n_pdf_review_gate(state: AppState) -> AppState:
    if state["autonomy_level"] >= 2 and state["score"] >= 4.3:
        return state                                              # auto-pass
    decision = _request_approval(state, "pdf_review",
                                 state["pdf_path"],
                                 f"PDF ready for {state['track']} track, score={state['score']}")
    if decision != "approved":
        return {**state, "errors": state["errors"] + ["pdf_review_rejected"]}
    return state

def n_apply(state: AppState) -> AppState:
    """Applier calls _request_approval internally at submit/2FA/account gates."""
    res = drive_application(
        state["jd_url"], state["pdf_path"], state["cover_path"], state["run_id"],
        approval_callback=lambda gate, shot, summary:
            _request_approval(state, gate, shot, summary),
    )
    return {**state, "ats_family": res["ats_family"]}

def n_verify(state: AppState) -> AppState:
    res = verify_submission(state["run_id"], state["jd_url"])
    return {**state, "errors": state["errors"] +
            ([] if res["confirmed"] else ["unverified_submission"])}

def _request_approval(state, gate, screenshot, summary) -> str:
    r = httpx.post("http://127.0.0.1:8765/internal/request_approval",
                   json={"run_id": state["run_id"], "gate": gate,
                         "screenshot_path": screenshot, "summary": summary,
                         "timeout_seconds": 1800}, timeout=2000)
    return r.json()["decision"]

def build_graph():
    g = StateGraph(AppState)
    g.add_node("score", n_score)
    g.add_node("tailor", n_tailor)
    g.add_node("pdf_gate", n_pdf_review_gate)
    g.add_node("apply", n_apply)
    g.add_node("verify", n_verify)
    g.add_edge(START, "score")
    g.add_conditional_edges("score", r_after_score, {"tailor": "tailor", "end": END})
    g.add_edge("tailor", "pdf_gate")
    g.add_edge("pdf_gate", "apply")
    g.add_edge("apply", "verify")
    g.add_edge("verify", END)
    saver = SqliteSaver.from_conn_string("db/careerops.db")
    return g.compile(checkpointer=saver)

if __name__ == "__main__":
    graph = build_graph()
    config = {"configurable": {"thread_id": "test-run-001"}}
    initial: AppState = {
        "run_id": "test-run-001", "jd_id": "JD-001",
        "jd_url": "https://boards.greenhouse.io/example/jobs/123",
        "jd_text": Path("jds/JD-001.txt").read_text(),
        "track": None, "score": None, "report_path": None,
        "pdf_path": None, "cover_path": None, "ats_family": None,
        "autonomy_level": 1, "errors": [],
        "gate_pending": None, "screenshot_path": None,
    }
    print(graph.invoke(initial, config))
```

### G.4 macOS Keychain wrapper (`agents/tools/keychain.py`)

```python
"""Keychain abstraction. Defaults to macOS Keychain via `keyring`.
Optional 1Password CLI (`op`) backend if CAREEROPS_VAULT=op."""
from __future__ import annotations
import os, subprocess, keyring

SERVICE_PREFIX = "careerops"

def _svc(name: str) -> str:
    return f"{SERVICE_PREFIX}.{name}"

def _backend() -> str:
    return os.environ.get("CAREEROPS_VAULT", "keychain").lower()

def get_secret(name: str, account: str = "default") -> str | None:
    backend = _backend()
    if backend == "keychain":
        return keyring.get_password(_svc(name), account)
    if backend == "op":
        ref = os.environ.get(f"CAREEROPS_OP_{name.upper()}",
                             f"op://careerops/{name}/password")
        try:
            return subprocess.check_output(["op", "read", ref], text=True).strip()
        except subprocess.CalledProcessError:
            return None
    if backend == "bw":
        try:
            return subprocess.check_output(["bw", "get", "password", name], text=True).strip()
        except subprocess.CalledProcessError:
            return None
    raise ValueError(f"Unknown CAREEROPS_VAULT: {backend}")

def set_secret(name: str, value: str, account: str = "default") -> None:
    if _backend() != "keychain":
        raise NotImplementedError("Use `op item create` or `bw create item` directly.")
    keyring.set_password(_svc(name), account, value)

def delete_secret(name: str, account: str = "default") -> None:
    if _backend() == "keychain":
        keyring.delete_password(_svc(name), account)

# Convenience accessors
def claude_api_key() -> str:          return get_secret("anthropic", "api_key")
def capsolver_key() -> str:           return get_secret("capsolver", "api_key")
def whatsapp_token() -> str:          return get_secret("whatsapp", "access_token")
def site_password(site: str) -> str:  return get_secret(f"site.{site}")
```

**Hardening:** after first write of each `careerops.*` item, open `Keychain Access.app` → Access Control tab → remove broad `python3` from "Always allow" → only the code-signed career-ops launchd-loaded binary will get prompt-free access. This closes the `jaraco/keyring` #457 default-allow-any-Python concern.

### G.5 Playwright + Computer Use hybrid harness (`agents/tools/browser_harness.py`)

```python
"""Hybrid browser harness: deterministic Playwright for known ATS; Computer
Use fallback for unknown forms. Stealth + persistent context per site."""
from __future__ import annotations
import asyncio, base64, time
from pathlib import Path
from typing import Callable
import anthropic
from playwright.async_api import async_playwright, BrowserContext, Page
from playwright_stealth import Stealth

ATS_DETECTORS = {
    "greenhouse": lambda url, html: "boards.greenhouse.io" in url or "greenhouse-iframe" in html,
    "lever":      lambda url, html: "jobs.lever.co" in url,
    "ashby":      lambda url, html: "jobs.ashbyhq.com" in url or "ashby_embed" in html,
    "workday":    lambda url, html: "myworkdayjobs.com" in url,
    "linkedin":   lambda url, html: "linkedin.com/jobs" in url,
    "indeed":     lambda url, html: "indeed.com" in url,
}

ctx_root = Path.home() / "Library/Application Support/career-ops/browser"

async def open_persistent(site_key: str, *, headless: bool = False) -> tuple[BrowserContext, Page]:
    ctx_dir = ctx_root / site_key
    ctx_dir.mkdir(parents=True, exist_ok=True)
    pw = await async_playwright().start()
    ctx = await pw.chromium.launch_persistent_context(
        user_data_dir=str(ctx_dir),
        channel="chrome",                       # real Chrome > bundled Chromium for fingerprint
        headless=headless,
        viewport={"width": 1440, "height": 900},
        locale="en-US",
        args=["--disable-blink-features=AutomationControlled"],
    )
    await Stealth().apply_stealth_async(ctx)
    page = ctx.pages[0] if ctx.pages else await ctx.new_page()
    return ctx, page

async def detect_ats(page: Page) -> str:
    html = await page.content()
    for name, fn in ATS_DETECTORS.items():
        if fn(page.url, html):
            return name
    return "generic"

async def human_type(page: Page, selector: str, text: str) -> None:
    await page.click(selector)
    for ch in text:
        await page.keyboard.type(ch, delay=70 + (hash(ch) % 60))     # 70–130 ms variable
    await asyncio.sleep(0.4 + (hash(text) % 100) / 250)               # 0.4–0.8 s tail

async def screenshot(page: Page, label: str, run_id: str) -> str:
    out = Path("audit") / run_id / f"{int(time.time())}-{label}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(out), full_page=True)
    return str(out)

# --- Computer Use fallback ---------------------------------------------
_client = anthropic.Anthropic()

async def computer_use_step(page: Page, instruction: str, run_id: str) -> str:
    shot_b64 = base64.b64encode(await page.screenshot(full_page=False)).decode()
    resp = _client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        tools=[{"type": "computer_20250124", "name": "computer",
                "display_width_px": 1440, "display_height_px": 900}],
        messages=[{"role": "user", "content": [
            {"type": "image",
             "source": {"type": "base64", "media_type": "image/png", "data": shot_b64}},
            {"type": "text", "text": instruction},
        ]}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "computer":
            action = block.input
            if action["action"] == "left_click":
                x, y = action["coordinate"]
                await page.mouse.click(x, y)
            elif action["action"] == "type":
                await page.keyboard.type(action["text"], delay=85)
            elif action["action"] == "key":
                await page.keyboard.press(action["text"])
            elif action["action"] == "screenshot":
                pass
    return resp.stop_reason or "ok"

# --- High-level harness ------------------------------------------------
async def apply_to_url(
    *,
    site_key: str,
    jd_url: str,
    pdf_path: str,
    profile: dict,
    cover_text: str,
    run_id: str,
    approval_callback: Callable[[str, str, str], str],
) -> dict:
    ctx, page = await open_persistent(site_key)
    try:
        await page.goto(jd_url, wait_until="domcontentloaded")
        await asyncio.sleep(1.5)
        ats = await detect_ats(page)

        from agents.adapters import REGISTRY
        adapter = REGISTRY.get(ats)
        if adapter:
            await adapter.run(page, pdf_path=pdf_path, profile=profile,
                              cover_text=cover_text, run_id=run_id,
                              human_type=human_type,
                              approve=approval_callback,
                              screenshot=lambda label: screenshot(page, label, run_id))
        else:
            for step in [
                "Find and click the apply button on this job page.",
                "Fill in name, email, phone from the form fields visible.",
                "Upload the resume file when prompted.",
                "Paste the cover letter into the cover-letter field if one exists.",
                "STOP at the final submit button — do not click it.",
            ]:
                await computer_use_step(page, step, run_id)

        shot = await screenshot(page, "pre-submit", run_id)
        decision = approval_callback("final_submit", shot,
                                     f"About to submit on {ats}. Confirm?")
        if decision == "approved":
            await page.get_by_role("button", name=lambda n: "submit" in n.lower()).click()
            await asyncio.sleep(3)
            await screenshot(page, "post-submit", run_id)
            return {"ats_family": ats, "submitted": True}
        return {"ats_family": ats, "submitted": False, "reason": decision}
    finally:
        await ctx.close()
```

A minimal Greenhouse adapter using this harness:

```python
# agents/adapters/ats_greenhouse.py
async def run(page, *, pdf_path, profile, cover_text, run_id,
              human_type, approve, screenshot):
    # Greenhouse forms have stable IDs: first_name, last_name, email, phone, resume
    await human_type(page, "input#first_name", profile["first_name"])
    await human_type(page, "input#last_name",  profile["last_name"])
    await human_type(page, "input#email",      profile["email"])
    await human_type(page, "input#phone",      profile["phone"])
    await page.set_input_files("input#resume", pdf_path)
    try:
        await page.fill("textarea#cover_letter", cover_text)
    except Exception:
        pass
    # School / work-auth / EEO handled by adapter using profile dict (omitted)
```

---

## Closing notes — operational expectations

- **Cost envelope at 30 apps/day average:** Claude API ~$0.30–$0.60/app for tailoring + Computer Use fallback (~$10–18/day, capped by routing cheap calls to local Qwen3); CapSolver ~$0.005/app worst case (~$0.15/day, well under your $5–10/month); WhatsApp Cloud API free at this volume; local LLM inference free.
- **Time envelope per app:** 90–180 s for known ATS (Greenhouse/Lever/Ashby), 4–8 min for Workday, plus your WhatsApp approval RTT.
- **First-commit PR sequence (concrete):** (1) `flake.nix` + `pyproject.toml` + `agents/` scaffold; (2) `agents/tools/keychain.py` + tests; (3) `agents/tools/gmail.py` + `make oauth` target; (4) `agents/tools/whatsapp.py` + `bridge/server.py` + Cloudflare-tunnel docs; (5) `agents/orchestrator/graph.py` skeleton + Greenhouse adapter; (6) `modes/apply.md` rewrite to dispatch to `localhost:8765`.
- **Single most important guardrail:** keep `request_human_approval("final_submit", ...)` in the code path until you have ≥100 successful submissions under autonomy ≤ 2 with zero "submitted wrong PDF" or "submitted to wrong company" defects. The repo's existing principle — *"the system never submits an application — you always have the final call"* — is the right default, and the autonomy ladder in `config/profile.yml` should be the only knob that relaxes it.
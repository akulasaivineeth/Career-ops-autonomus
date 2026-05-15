# NEXT STEPS — Career-ops-autonomus

> Your personal runbook. Everything you need to go from "repo cloned" to "first application submitted autonomously."

---

## ❓ Where Are We Right Now?

**Repository:** `https://github.com/akulasaivineeth/Career-ops-autonomus`  
**Branch to work from:** `main` (everything is merged here)  
**Code status:** All 48 BUILD.md tasks scaffolded and tested (56+ unit tests pass in CI)  
**What still needs your Mac:** Secrets, browser sessions, Nix lock, first live apply  

```
career-ops-autonomus/
├── BUILD.md            ← single source of truth for task progress (read this first)
├── NEXT_STEPS.md       ← THIS FILE
├── CLAUDE.md           ← agent instructions (auto-read by Claude Code)
├── AGENTS.md           ← hard rules agents must follow
├── DATA_CONTRACT.md    ← who owns which files
├── LEGAL_DISCLAIMER.md ← ToS / automation rules
│
├── agents/             ← Python: LangGraph orchestrator, workers, adapters, tools
├── bridge/             ← FastAPI control plane (localhost:8765)
├── db/                 ← SQLite migrations + runtime DB (gitignored)
├── cv/                 ← YOUR resume tracks (YOU fill these in)
├── config/             ← profile.yml (YOUR targets, autonomy settings)
├── data/               ← applications.xlsx + pipeline.xlsx (live tracking)
├── docs/               ← setup guides per integration
├── infra/              ← launchd plists for macOS scheduling
├── bin/                ← career-apply, career-ops-daily (shell entrypoints)
├── modes/              ← Claude Code modes (apply.md = bridge dispatcher)
└── scripts/            ← migration helpers, LinkedIn session saver
```

---

## 🗝️ Step 0 — Secrets You Must Store in Keychain

> Run each command **in YOUR terminal on your Mac** (never paste secrets into chat).

### Required before anything works

```bash
# 1. Anthropic Claude API key (https://console.anthropic.com → API Keys)
read -s VAL && security add-generic-password -U \
  -s careerops.anthropic -a api_key -w "$VAL" && unset VAL && echo stored
```

### Required for HITL approvals and submission verification

```bash
# 2. WhatsApp Cloud API permanent token
#    (developers.facebook.com → Your App → WhatsApp → API Setup → System Users → permanent token)
read -s VAL && security add-generic-password -U \
  -s careerops.whatsapp -a access_token -w "$VAL" && unset VAL && echo stored
```

### Required for Gmail verification-code extraction

```bash
# 3. Gmail OAuth — NOT a password. Run the flow once after cloning:
make oauth-gmail
# This opens a browser, you consent, the refresh token is sealed in Keychain automatically.
# (Requires ~/.career-ops/gmail-credentials.json — see docs/GMAIL_SETUP.md)
```

### Optional (CAPTCHA solving — needed for Indeed/Glassdoor/LinkedIn at volume)

```bash
# 4. CapSolver (https://dashboard.capsolver.com → API)
read -s VAL && security add-generic-password -U \
  -s careerops.capsolver -a api_key -w "$VAL" && unset VAL && echo stored

# 5. 2Captcha fallback (https://2captcha.com → API)
read -s VAL && security add-generic-password -U \
  -s careerops.twocaptcha -a api_key -w "$VAL" && unset VAL && echo stored
```

### Verify all secrets are stored

```bash
security find-generic-password -s careerops.anthropic -a api_key -w >/dev/null && echo "✅ Anthropic"
security find-generic-password -s careerops.whatsapp  -a access_token -w >/dev/null && echo "✅ WhatsApp"
security find-generic-password -s careerops.gmail     -a oauth_token_json -w >/dev/null && echo "✅ Gmail"
```

---

## 🖥️ Step 1 — Clone and Set Up the Repo on Your Mac

```bash
# 1. Clone
git clone https://github.com/akulasaivineeth/Career-ops-autonomus.git ~/code/career-ops
cd ~/code/career-ops

# 2. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.zshrc   # or restart terminal

# 3. Install Python dependencies
uv sync --all-groups

# 4. Install Playwright Chromium browser
uv run playwright install chromium

# 5. Run migrations (creates db/careerops.db)
uv run python -m db.migrate

# 6. Run all tests (should be 63 passing)
uv run pytest -q

# 7. Run the doctor check
npm install && npm run doctor
```

**Where to find it:**
- Repo root: `~/code/career-ops/`
- Python venv: `~/code/career-ops/.venv/`
- SQLite DB: `~/code/career-ops/db/careerops.db` (gitignored)

---

## 📄 Step 2 — Fill In Your CV Tracks

> These files live at `cv/da.md`, `cv/mle.md`, `cv/de.md`.  
> **The agent reads them but NEVER writes to them.** You own them entirely.

```bash
open ~/code/career-ops/cv/mle.md   # in any editor
open ~/code/career-ops/cv/da.md
open ~/code/career-ops/cv/de.md
```

**What to put in each file:**
- `mle.md` = ML Engineer track (Python, PyTorch, LLMs, MLOps, etc.)
- `da.md`  = Data Analyst track (SQL, Tableau, A/B testing, dbt, etc.)
- `de.md`  = Data Engineer track (Spark, Kafka, dbt, Snowflake, etc.)

Fill in every section marked `[YOUR NAME]` / `[placeholder]`. Quantify bullets with %, $, user counts.  
See `docs/CV_TRACKS.md` for the full guide.

---

## ⚙️ Step 3 — Configure Your Profile

Edit `config/profile.yml` — this drives every apply decision:

```bash
open ~/code/career-ops/config/profile.yml
```

Key fields to fill:

| Field | What it controls |
|-------|-----------------|
| `identity.display_name` | Your name on cover letters and form fields |
| `identity.email` | Applied to every form |
| `identity.phone` | Applied to every form |
| `identity.first_name` / `last_name` | Greenhouse/Lever form fields |
| `comp.currency` / `comp.min_floor` | Kill-signal: auto-reject roles below this |
| `allowed_locations` | Kill-signal: auto-reject wrong locations |
| `deal_breakers` | Keywords that trigger auto-reject |
| `autonomy.level` | Start at `1` (approve everything) |
| `gmail_account` | Your Gmail address |
| `whatsapp_number` | Your WhatsApp phone (e.g. `+1XXXXXXXXXX`) |

---

## 📬 Step 4 — Set Up WhatsApp HITL

Follow `docs/WHATSAPP_SETUP.md` — the full guide is there. Summary:

1. Create a Meta Business app at [developers.facebook.com](https://developers.facebook.com)
2. Add WhatsApp product → get your **Phone Number ID**
3. Set env vars in `~/.zshrc`:
   ```bash
   export WA_PHONE_NUMBER_ID=<id>
   export WA_USER_NUMBER=+1XXXXXXXXXX
   export WA_WEBHOOK_VERIFY_TOKEN=<32-char random string>
   ```
4. Store token in Keychain (Step 0 above)
5. Expose the bridge for webhooks (one-time):
   ```bash
   brew install cloudflared
   cloudflared tunnel --url http://127.0.0.1:8765
   # Set the resulting URL as the webhook in Meta dashboard
   ```

**Where to find it:** `docs/WHATSAPP_SETUP.md`

---

## 📧 Step 5 — Set Up Gmail OAuth (verification + confirmation emails)

Follow `docs/GMAIL_SETUP.md`. Summary:

1. Google Cloud Console → create project → enable Gmail API
2. OAuth consent screen → Desktop app → download `client_secret_*.json`
3. Save it:
   ```bash
   mkdir -p ~/.career-ops && chmod 700 ~/.career-ops
   mv ~/Downloads/client_secret_*.json ~/.career-ops/gmail-credentials.json
   chmod 600 ~/.career-ops/gmail-credentials.json
   ```
4. Run the OAuth flow (browser consent, one-time):
   ```bash
   cd ~/code/career-ops && make oauth-gmail
   # Opens browser → consent → token sealed in Keychain automatically
   ```

**Where to find it:** `docs/GMAIL_SETUP.md`

---

## 🌐 Step 6 — Capture LinkedIn Session (one-time)

Follow `docs/LINKEDIN_SESSION.md`. Summary:

```bash
cd ~/code/career-ops
node scripts/save-linkedin-session.mjs
# Opens Chrome → log in → close window → session saved
```

Session saved at: `~/Library/Application Support/career-ops/browser/linkedin/state.json`

**Refresh required:** The session expires (~30 days). The healthcheck cron will alert you via WhatsApp when it does.  
**Where to find it:** `docs/LINKEDIN_SESSION.md`

---

## 🧪 Step 7 — Run Your First Test Apply

```bash
# Terminal 1 — start the bridge
cd ~/code/career-ops && uv run python -m bridge

# Terminal 2 — dispatch a test apply
bin/career-apply "https://boards.greenhouse.io/stripe/jobs/123456"
# Outputs: run_id, poll URL, approve/reject commands

# Check state
curl http://127.0.0.1:8765/state/<run_id>

# Approve via CLI (if WhatsApp not set up yet)
curl -X POST http://127.0.0.1:8765/approve/<run_id>
```

**What happens:**
1. Scorer evaluates the JD → picks DA/MLE/DE track
2. Tailor generates PDF + cover letter
3. Bridge sends WhatsApp "approve PDF?" message
4. On approval → browser opens, fills form, stops before submit
5. Bridge sends WhatsApp "approve submit?" message + screenshot
6. On approval → clicks Submit → Verifier polls Gmail for confirmation

---

## 📊 Step 8 — View Your Tracked Applications (Excel)

Two Excel files are auto-updated by the agent:

| File | What it shows | Open with |
|------|--------------|-----------|
| `data/applications.xlsx` | Every application (status, score, company, role, screenshot dir) | Excel / Numbers |
| `data/pipeline.xlsx` | JDs queued for scoring and apply | Excel / Numbers |

```bash
open ~/code/career-ops/data/applications.xlsx   # Numbers/Excel
open ~/code/career-ops/data/pipeline.xlsx

# Or view in terminal:
uv run python -m agents.tools.tracker

# Sync SQLite → Excel manually at any time:
uv run python -c "from agents.tools.tracker import sync_from_db; sync_from_db()"
```

**Colour coding in Excel:**

| Colour | Status |
|--------|--------|
| 🟢 Light green | `submitted` |
| 🔴 Light red | `apply_failed` |
| 🟡 Yellow | `awaiting_approval` |
| ⚪ Grey | `rejected_auto` |
| 🔵 Light cyan | `queued` |
| 🟠 Peach | `scoring` |
| 🔵 Powder blue | `applying` |

---

## ⏰ Step 9 — Schedule Daily Automation (optional)

```bash
cd ~/code/career-ops
bash infra/install-launchd.sh
```

This loads three launchd jobs:

| Job | Schedule | What it does |
|-----|----------|-------------|
| `com.career-ops.daily` | Weekdays 09:00 | Scan → score → queue applies (HITL still required for each submit) |
| `com.career-ops.weekly` | Sundays 18:00 | WhatsApp digest (apps this week, response rate, spend) |
| `com.career-ops.healthcheck` | Every 6h | Checks browser sessions, alerts via WhatsApp if expired |

Logs: `~/Library/Logs/career-ops/`  
Check status: `launchctl list | grep com.career-ops`  
**Where to find it:** `docs/SCHEDULING.md`

---

## 🔑 Step 10 — Set Up Nix Dev Shell (optional but recommended for reproducibility)

```bash
# Install Nix (one-time)
sh <(curl -L https://nixos.org/nix/install) --daemon

# Enable flakes
echo 'experimental-features = nix-command flakes' >> ~/.config/nix/nix.conf

# Generate flake.lock (pins exact versions)
cd ~/code/career-ops
nix flake lock    # generates flake.lock
git add flake.lock && git commit -m "chore(0.1): pin flake.lock"
git push origin main

# Enter pinned dev shell from now on
nix develop       # or `direnv allow` after `use flake` in .envrc
```

**Where to find it:** `flake.nix`, `BUILD.md Task 0.1`

---

## 🗺️ Where Everything Lives — Quick Reference

| What | Path | Notes |
|------|------|-------|
| Build plan + task list | `BUILD.md` | Read at the start of every session |
| Your CV tracks | `cv/da.md`, `cv/mle.md`, `cv/de.md` | YOU edit; agent reads only |
| Your search profile | `config/profile.yml` | Targets, comp floor, autonomy level |
| Application tracking | `data/applications.xlsx` | Auto-updated by agent |
| JD pipeline | `data/pipeline.xlsx` | Auto-updated by scanner |
| JD text dumps | `jds/<id>.txt` | One file per discovered JD |
| Score reports | `reports/<NNN>-<slug>-<date>.md` | Generated by Scorer |
| Audit screenshots | `audit/<run_id>/` | One folder per apply attempt |
| Generated PDFs | `output/<run_id>.pdf` | Tailored CV per application |
| Secrets | macOS Keychain, prefix `careerops.*` | NEVER in files |
| Gmail client JSON | `~/.career-ops/gmail-credentials.json` | OUTSIDE repo |
| Browser sessions | `~/Library/Application Support/career-ops/browser/` | OUTSIDE repo |
| Agent source code | `agents/` | Orchestrator, workers, adapters, tools |
| Bridge source code | `bridge/` | FastAPI control plane |
| DB schema | `db/migrations/` | Applied by `python -m db.migrate` |
| Docs guides | `docs/` | SECRETS, GMAIL, WHATSAPP, LINKEDIN, SCHEDULING, ENCRYPTION, CV_TRACKS |
| Logs (scheduled) | `~/Library/Logs/career-ops/` | macOS launchd output |

---

## ⚠️ Hard Rules — Never Break These

1. **No final submit without your explicit approval** — every application goes through WhatsApp before clicking Submit.
2. **No LinkedIn profile scraping** — Easy Apply only, ≤8/hr ≤25/day.
3. **No secrets in the repo** — all credentials via Keychain, never `.env` files.
4. **No fake accounts / proxy networks** — one human, one identity.
5. **Autonomy level 1 to start** — approve every gate until you trust the system.
6. **`data/applications.xlsx` is yours** — the agent appends/updates, never bulk-wipes.

---

## 🚦 What Happens at Each Autonomy Level

Set `autonomy.level` in `config/profile.yml`:

| Level | Name | What requires your approval |
|-------|------|------------------------------|
| `0` | Dry-run | Everything (browser never opens) |
| `1` | Approve all | PDF review, account creation, 2FA, **submit** |
| `2` | Approve submit only | PDF auto-passes if score ≥ 4.3 + track stable |
| `3` | Approve anomalies | Non-standard questions or unknown ATS → HITL |
| `4` | Full auto | All gates can auto-pass per rules table |

**Start at level 1.** Raise only after you've watched several successful level-1 runs.

---

## 🆘 Troubleshooting

| Problem | Where to look | Fix |
|---------|--------------|-----|
| Bridge not running | Check terminal running `uv run python -m bridge` | Start it |
| WhatsApp not receiving | Check `WA_PHONE_NUMBER_ID` env, cloudflared tunnel | `docs/WHATSAPP_SETUP.md` |
| Gmail token expired | `make oauth-gmail` | Re-run OAuth flow |
| LinkedIn session expired | WhatsApp healthcheck alert | `node scripts/save-linkedin-session.mjs` |
| CAPTCHA failing | CapSolver balance or key | Top up at dashboard.capsolver.com |
| Score always < 4.0 | Check `cv/*.md` skills vs JD | Fill in CV tracks (Step 2) |
| PDF blank | `generate-pdf.mjs` missing | Vendor from `santifer/career-ops` (see BUILD.md) |
| DB locked | Multiple bridge instances | `pkill -f "python -m bridge"` then restart |

---

## 📞 Quick-Start Checklist

```
[ ] Repo cloned to ~/code/career-ops
[ ] uv sync --all-groups && uv run playwright install chromium
[ ] uv run python -m db.migrate
[ ] uv run pytest -q  (63 tests should pass)
[ ] Anthropic key stored in Keychain
[ ] config/profile.yml filled (name, email, targets)
[ ] cv/mle.md (and/or da.md, de.md) filled with real experience
[ ] Gmail client JSON at ~/.career-ops/gmail-credentials.json
[ ] make oauth-gmail (runs once, stores token)
[ ] WhatsApp env vars set + cloudflared tunnel running
[ ] WhatsApp token in Keychain
[ ] node scripts/save-linkedin-session.mjs (LinkedIn only)
[ ] uv run python -m bridge (bridge running)
[ ] bin/career-apply <test_greenhouse_url>
[ ] Approve PDF via WhatsApp → approve Submit → check applications.xlsx
[ ] bash infra/install-launchd.sh (optional, for daily scheduling)
```

---

*Generated: 2026-05-15. Update this file when your setup changes.*

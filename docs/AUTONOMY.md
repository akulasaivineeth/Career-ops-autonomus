# Autonomy ladder

Human-in-the-loop (HITL) behavior is controlled by **`autonomy.level`** in `config/profile.yml` and enforced in code via LangGraph `interrupt()` gates (see architecture artifact §B.4 and `BUILD.md` Phase 4).

## Levels (0–4)

| Level | Name | Behavior summary |
|------:|------|------------------|
| **0** | Dry-run | No browser submits; logs planned actions only. |
| **1** | Approve everything | Every gate (PDF review, account creation, 2FA, final submit) requires explicit approval. |
| **2** | Approve submit only | PDF review may auto-pass when score and track match policy; **final submit** still HITL. |
| **3** | Approve anomalies only | Known-good flows proceed; non-standard questions / unknown ATS paths force HITL. |
| **4** | Full auto | Maximum automation allowed by policy — still **must** respect site ToS and legal guardrails. |

## Gate table (typical defaults)

| Gate | Level 0–1 | Level 2 | Level 3–4 |
|------|-----------|---------|-----------|
| PDF ready | HITL | Auto if track stable + score policy | Tighter anomaly checks |
| Account creation | HITL | HITL | HITL unless explicitly relaxed |
| 2FA / SMS | HITL | HITL (Gmail code auto-read only if `twofa: auto_gmail`) | Same |
| Final submit | HITL | HITL | Policy-driven; never skip audit trail |
| CAPTCHA after 3 failures | HITL | HITL | HITL |

## Timeouts (WhatsApp / mobile HITL)

Default: **30 minutes** pending user response → escalate; **2 hours** no response → auto-pause that source (architecture §E.4). Tune in `bridge/approvals.py` when Task 1.7 lands.

## Operational rule

Until autonomy code is fully wired, treat the repo as **level 1**: assume every risky step needs a human.

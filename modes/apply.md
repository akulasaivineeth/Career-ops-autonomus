# /apply — Dispatch to Python Orchestrator

> BUILD.md Task 1.8. Rewritten from "fill forms yourself" to a dispatcher that hands off to the bridge.

**Mode name:** apply  
**Invocation:** `/apply <jd_id_or_url>`

## Behavior

1. Verify the bridge is running:
   ```bash
   curl http://127.0.0.1:8765/health
   ```
   If not: instruct the user to run `uv run python -m bridge` in a separate terminal.

2. POST to `/run` with the JD:
   ```bash
   curl -X POST http://127.0.0.1:8765/run \
     -H "Content-Type: application/json" \
     -d '{"jd_id":"<id>","jd_url":"<url>"}'
   ```

3. Poll `/state/<run_id>` every 5 s and stream updates to the user.

4. Await WhatsApp approval events — bridge handles all gate notifications.

## Hard rules (never bypass)

- Do NOT directly open a browser or fill forms in this mode.
- All browser work runs inside `agents/tools/browser_harness.py` via the bridge.
- All submission gates go through `bridge/approvals.py::request_approval`.

## Status messages

| State | Message |
|-------|---------|
| `queued` | Run started, waiting for scorer… |
| `scoring` | Scoring JD… |
| `rejected_auto` | Score below 4.0 or kill signal — skipped. |
| `tailoring` | Generating tailored PDF… |
| `awaiting_approval` | Waiting for your WhatsApp approval… |
| `applying` | Browser filling form… |
| `submitted` | Application submitted ✅ |
| `apply_failed` | Submission failed — check audit log. |

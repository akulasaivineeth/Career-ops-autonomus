# Gmail API setup

1. Complete **Task −1.6** in `BUILD.md` (OAuth **client** JSON outside the repo under `~/.career-ops/gmail-credentials.json`, or set `GMAIL_CREDENTIALS_PATH`).
2. Run **`make oauth-gmail`** (runs `uv run python -m agents.tools.gmail`) to open the browser consent flow and store the **refresh token** in Keychain as `careerops.gmail` / `oauth_token_json`.
3. Scopes are intentionally narrow: **`gmail.readonly`** + **`gmail.modify`** (no send).

Helpers in `agents/tools/gmail.py`: `search`, `get_body_text`, `mark_read`, `get_verification_code` (all require an authenticated `service` from `get_service()`).

Until OAuth completes, `get_service()` raises a clear `RuntimeError`.

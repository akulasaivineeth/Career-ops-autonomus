# Gmail API setup

1. Complete **Task −1.6** in `BUILD.md` (OAuth **client** JSON outside the repo under `~/.career-ops/`).
2. Run **`make oauth-gmail`** once that target is implemented (BUILD.md **Task 0.5**) to store the **refresh token** in Keychain as `careerops.gmail` / `oauth_token_json`.
3. Scopes are intentionally narrow: **`gmail.readonly`** + **`gmail.modify`** (no send).

Until Task 0.5 ships, `agents.tools.gmail.get_service()` will raise a clear `RuntimeError` if no token is present.

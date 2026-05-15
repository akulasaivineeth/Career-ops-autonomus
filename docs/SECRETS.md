# Secrets handling

All API keys, OAuth tokens, and site passwords go through **`agents.tools.keychain`**, which uses the OS default `keyring` backend unless you opt into CLI vault reads:

- **macOS:** Keychain Access (`careerops.*` service prefix).
- **Linux CI:** Secret Service or file backend depending on environment — production HITL stack targets macOS per `BUILD.md`.

## Adding a secret (human operator)

The agent must **never** ask you to paste a secret into chat. Use the **Secret-Prompt Protocol** in `BUILD.md`: run the `security add-generic-password` one-liner locally so the value never touches the repo or logs.

## `CAREEROPS_VAULT`

| Value | Read path | Write path (`set_secret`) |
|-------|-----------|---------------------------|
| `keychain` (default) | `keyring` / Keychain | `keyring` |
| `op` | 1Password CLI: `op read` using env refs below | **Still** `keyring` (use `op` CLI yourself for item creation) |
| `bw` | Bitwarden CLI: `bw get password …` | **Still** `keyring` |

OAuth refresh tokens created by `make oauth-gmail` are always written with `set_secret` → **Keychain**, so `get_service()` continues to work when `CAREEROPS_VAULT=op` for *other* secrets.

### 1Password (`op`)

Set `CAREEROPS_VAULT=op` and define one reference per logical secret:

- Pattern: `CAREEROPS_OP_REF__<LOGICAL_NAME>__<ACCOUNT>`
- Example for `get_secret("anthropic", "api_key")`:  
  `CAREEROPS_OP_REF__ANTHROPIC__API_KEY=op://Private/Anthropic/credential`

### Bitwarden (`bw`)

Set `CAREEROPS_VAULT=bw` (session must be unlocked) and:

- Pattern: `CAREEROPS_BW_ITEM__<LOGICAL_NAME>__<ACCOUNT>` = item id or name passed to `bw get password <item>`.

## Keychain ACL hardening

Restrict which binaries may read each item via **Keychain Access → item → Access Control**. This mitigates broad-read risks discussed in the broader `jaraco/keyring` ecosystem.

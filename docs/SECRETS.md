# Secrets handling

All API keys, OAuth tokens, and site passwords go through **`agents.tools.keychain`**, which uses the OS default `keyring` backend:

- **macOS:** Keychain Access (`careerops.*` service prefix).
- **Linux CI:** in-memory / Secret Service depending on environment — production use is macOS per BUILD.md.

## Adding a secret (human operator)

The agent must **never** ask you to paste a secret into chat. Use the **Secret-Prompt Protocol** in `BUILD.md`: run the `security add-generic-password` one-liner locally so the value never touches the repo or logs.

## Optional backends

Set `CAREEROPS_VAULT` to `keychain` (default), `op` (1Password CLI), or `bw` (Bitwarden) when those integrations are implemented (BUILD.md Task 0.4+).

## Keychain ACL hardening

Restrict which binaries may read each item via **Keychain Access → item → Access Control**. This mitigates broad-read risks discussed in the broader `jaraco/keyring` ecosystem.

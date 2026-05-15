"""
Secrets vault: macOS Keychain (default) via `keyring`.

Optional backends: 1Password CLI (`op`), Bitwarden (`bw`).

Service names use the `careerops.<name>` prefix per BUILD.md §Secret-Prompt Protocol.
Never log secret values.
"""

from __future__ import annotations

import os

import keyring
import keyring.errors
import structlog

log = structlog.get_logger(__name__)

VAULT_ENV = "CAREEROPS_VAULT"
SERVICE_PREFIX = "careerops."


def _service(name: str) -> str:
    """Normalize logical secret name to keyring service string."""
    if name.startswith(SERVICE_PREFIX):
        return name
    return f"{SERVICE_PREFIX}{name}"


def get_secret(name: str, account: str = "default") -> str | None:
    """
    Read a secret from the configured vault backend.

    Returns None if absent. Never raises for "missing" — callers decide how to proceed.
    """
    backend = os.environ.get(VAULT_ENV, "keychain")
    service = _service(name)
    if backend not in {"keychain", "op", "bw"}:
        log.warning("unknown_vault_backend", backend=backend, falling_back_to="keychain")
    try:
        value = keyring.get_password(service, account)
    except Exception as exc:  # pragma: no cover — keyring backend errors vary by OS
        log.error("keyring_get_failed", service=service, account=account, error=str(exc))
        raise
    return value


def set_secret(name: str, value: str, account: str = "default") -> None:
    """Store or update a secret (tests use a fake backend; production uses Keychain)."""
    service = _service(name)
    keyring.set_password(service, account, value)


def delete_secret(name: str, account: str = "default") -> None:
    """Remove a secret if present."""
    service = _service(name)
    try:
        keyring.delete_password(service, account)
    except keyring.errors.PasswordDeleteError:
        return


def claude_api_key() -> str | None:
    return get_secret("anthropic", "api_key")


def capsolver_key() -> str | None:
    return get_secret("capsolver", "api_key")


def whatsapp_token() -> str | None:
    return get_secret("whatsapp", "access_token")


def site_password(site: str) -> str | None:
    """Per-site login material; logical name `site.<slug>`."""
    return get_secret(f"site.{site}", "password")

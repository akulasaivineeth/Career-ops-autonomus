"""
Secrets vault: macOS Keychain (default) via `keyring`.

Optional read paths: 1Password CLI (`op`), Bitwarden CLI (`bw`) via ``CAREEROPS_VAULT``.

``set_secret`` / ``delete_secret`` always use ``keyring`` so OAuth tokens can be stored consistently
after ``make oauth-gmail`` even when reads use ``op``/``bw`` (see docs/SECRETS.md).
"""

from __future__ import annotations

import os
import subprocess
from typing import Final

import keyring
import keyring.errors
import structlog

log = structlog.get_logger(__name__)

VAULT_ENV: Final = "CAREEROPS_VAULT"
SERVICE_PREFIX: Final = "careerops."


def _service(name: str) -> str:
    """Normalize logical secret name to keyring service string."""
    if name.startswith(SERVICE_PREFIX):
        return name
    return f"{SERVICE_PREFIX}{name}"


def _op_env_ref(logical_name: str, account: str) -> str | None:
    """1Password `op read` reference, e.g. ``op://Private/Anthropic/credential``."""
    key = f"CAREEROPS_OP_REF__{logical_name.upper()}__{account.upper()}"
    return os.environ.get(key)


def _bw_env_item(logical_name: str, account: str) -> str | None:
    """Bitwarden item id or name for ``bw get password <item>``."""
    key = f"CAREEROPS_BW_ITEM__{logical_name.upper()}__{account.upper()}"
    return os.environ.get(key)


def _read_1password(logical_name: str, account: str) -> str | None:
    ref = _op_env_ref(logical_name, account)
    if not ref:
        return None
    proc = subprocess.run(
        ["op", "read", ref, "--no-newline"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        log.warning("op_read_failed", ref=ref, stderr=proc.stderr[:200])
        return None
    return proc.stdout or None


def _read_bitwarden(logical_name: str, account: str) -> str | None:
    item = _bw_env_item(logical_name, account)
    if not item:
        return None
    proc = subprocess.run(
        ["bw", "get", "password", item, "--nointeraction"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        log.warning("bw_read_failed", item=item, stderr=proc.stderr[:200])
        return None
    return proc.stdout.strip() or None


def get_secret(name: str, account: str = "default") -> str | None:
    """
    Read a secret from the configured vault backend.

    Returns None if absent. Never raises for "missing" — callers decide how to proceed.
    """
    backend = os.environ.get(VAULT_ENV, "keychain").lower()
    if backend not in {"keychain", "op", "bw"}:
        log.warning("unknown_vault_backend", backend=backend, falling_back_to="keychain")
        backend = "keychain"

    if backend == "op":
        val = _read_1password(name, account)
        if val is not None:
            return val
        return None

    if backend == "bw":
        val = _read_bitwarden(name, account)
        if val is not None:
            return val
        return None

    service = _service(name)
    try:
        return keyring.get_password(service, account)
    except keyring.errors.NoKeyringError:
        log.warning("keyring_no_backend", service=service, account=account)
        return None
    except Exception as exc:  # pragma: no cover — keyring backend errors vary by OS
        log.error("keyring_get_failed", service=service, account=account, error=str(exc))
        raise


def set_secret(name: str, value: str, account: str = "default") -> None:
    """Persist via OS keyring (Keychain on macOS)."""
    service = _service(name)
    keyring.set_password(service, account, value)


def delete_secret(name: str, account: str = "default") -> None:
    """Remove from OS keyring if present."""
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
    """Per-site login material; logical name ``site.<slug>``."""
    return get_secret(f"site.{site}", "password")

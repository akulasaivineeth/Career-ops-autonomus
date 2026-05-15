"""Tests for ``agents.tools.keychain`` — uses in-memory monkeypatch, no real Keychain."""

from __future__ import annotations

import pytest

import agents.tools.keychain as kc


def test_roundtrip_set_get_delete(monkeypatch: pytest.MonkeyPatch) -> None:
    vault: dict[tuple[str, str], str] = {}

    def get_password(service: str, username: str) -> str | None:
        return vault.get((service, username))

    def set_password(service: str, username: str, password: str) -> None:
        vault[(service, username)] = password

    def delete_password(service: str, username: str) -> None:
        vault.pop((service, username), None)

    monkeypatch.setattr(kc.keyring, "get_password", get_password)
    monkeypatch.setattr(kc.keyring, "set_password", set_password)
    monkeypatch.setattr(kc.keyring, "delete_password", delete_password)

    assert kc.get_secret("anthropic", "api_key") is None
    kc.set_secret("anthropic", "secret-value", "api_key")
    assert kc.get_secret("anthropic", "api_key") == "secret-value"
    kc.delete_secret("anthropic", "api_key")
    assert kc.get_secret("anthropic", "api_key") is None

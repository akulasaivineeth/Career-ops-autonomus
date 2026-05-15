"""CAPTCHA tool tests — mocked HTTP (BUILD.md Task 2.8)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agents.tools import captcha as cap_mod
from agents.tools.captcha import CaptchaEscalateError, _failures


def _reset_failures() -> None:
    _failures.clear()


def test_capsolver_path_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_failures()

    monkeypatch.setattr(cap_mod, "_capsolver_solve", lambda *a, **k: "TOKEN-123")
    import agents.tools.keychain as _kc

    monkeypatch.setattr(_kc, "capsolver_key", lambda: "fake-capsolver-key")
    monkeypatch.setattr(_kc, "get_secret", lambda *a, **k: None)

    token = cap_mod.captcha_solve("recaptcha_v2", "site-key", "https://example.com", run_id="r1")
    assert token == "TOKEN-123"
    assert _failures["r1"] == 0


def test_escalate_after_two_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_failures()

    monkeypatch.setattr(cap_mod, "_capsolver_solve", MagicMock(side_effect=RuntimeError("fail")))
    monkeypatch.setattr(cap_mod, "_2captcha_solve", MagicMock(side_effect=RuntimeError("fail")))
    import agents.tools.keychain as _kc

    monkeypatch.setattr(_kc, "capsolver_key", lambda: "key")
    monkeypatch.setattr(_kc, "get_secret", lambda *a, **k: "tc-key")

    with pytest.raises(RuntimeError):
        cap_mod.captcha_solve("turnstile", "sk", "https://x.com", run_id="r2")

    assert _failures["r2"] == 1

    with pytest.raises(CaptchaEscalateError):
        cap_mod.captcha_solve("turnstile", "sk", "https://x.com", run_id="r2")

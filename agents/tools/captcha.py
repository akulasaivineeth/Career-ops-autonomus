"""
CAPTCHA solver: CapSolver (primary) with 2Captcha fallback (BUILD.md Task 2.8).

Raises ``CaptchaEscalateError`` after 2 consecutive failures for the same run_id.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Literal

import httpx
import structlog

log = structlog.get_logger(__name__)

CaptchaType = Literal["recaptcha_v2", "recaptcha_v3", "turnstile", "hcaptcha"]

_CAPSOLVER_URL = "https://api.capsolver.com"
_2CAPTCHA_URL = "https://2captcha.com/in.php"

_failures: dict[str, int] = defaultdict(int)


class CaptchaEscalateError(Exception):
    """Raised after 2 consecutive captcha failures for one run_id."""


def _capsolver_solve(captcha_type: CaptchaType, site_key: str, page_url: str, api_key: str) -> str:
    task_map = {
        "recaptcha_v2": "ReCaptchaV2Task",
        "recaptcha_v3": "ReCaptchaV3Task",
        "turnstile": "AntiTurnstileTask",
        "hcaptcha": "HCaptchaTask",
    }
    resp = httpx.post(
        f"{_CAPSOLVER_URL}/createTask",
        json={
            "clientKey": api_key,
            "task": {
                "type": task_map[captcha_type],
                "websiteURL": page_url,
                "websiteKey": site_key,
            },
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("errorId"):
        raise RuntimeError(f"CapSolver error: {data.get('errorDescription')}")
    task_id = data["taskId"]

    import time

    for _ in range(60):
        time.sleep(2)
        result = httpx.post(
            f"{_CAPSOLVER_URL}/getTaskResult",
            json={"clientKey": api_key, "taskId": task_id},
            timeout=30,
        ).json()
        if result.get("status") == "ready":
            return result["solution"]["gRecaptchaResponse"]
    raise TimeoutError("CapSolver task timed out.")


def _2captcha_solve(captcha_type: CaptchaType, site_key: str, page_url: str, api_key: str) -> str:
    method_map = {
        "recaptcha_v2": "userrecaptcha",
        "recaptcha_v3": "userrecaptcha",
        "turnstile": "turnstile",
        "hcaptcha": "hcaptcha",
    }
    resp = httpx.get(
        _2CAPTCHA_URL,
        params={
            "key": api_key,
            "method": method_map[captcha_type],
            "googlekey": site_key,
            "pageurl": page_url,
            "json": 1,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != 1:
        raise RuntimeError(f"2Captcha error: {data.get('request')}")
    request_id = data["request"]

    import time

    for _ in range(60):
        time.sleep(5)
        result = httpx.get(
            "https://2captcha.com/res.php",
            params={"key": api_key, "action": "get", "id": request_id, "json": 1},
            timeout=30,
        ).json()
        if result.get("status") == 1:
            return result["request"]
        if result.get("request") not in ("CAPCHA_NOT_READY", "CAPTCHA_NOT_READY"):
            raise RuntimeError(f"2Captcha error: {result.get('request')}")
    raise TimeoutError("2Captcha task timed out.")


def captcha_solve(
    captcha_type: CaptchaType,
    site_key: str,
    page_url: str,
    *,
    run_id: str = "global",
) -> str:
    """
    Solve a CAPTCHA. CapSolver first; 2Captcha fallback.

    Raises ``CaptchaEscalateError`` after 2 consecutive failures for ``run_id``.
    """
    from agents.tools import keychain as _kc

    cs_key = _kc.capsolver_key()
    tc_key = _kc.get_secret("twocaptcha", "api_key")

    errors: list[str] = []

    if cs_key:
        try:
            token = _capsolver_solve(captcha_type, site_key, page_url, cs_key)
            _failures[run_id] = 0
            return token
        except Exception as exc:
            errors.append(f"capsolver:{exc}")
            log.warning("capsolver_failed", run_id=run_id, error=str(exc))

    if tc_key:
        try:
            token = _2captcha_solve(captcha_type, site_key, page_url, tc_key)
            _failures[run_id] = 0
            return token
        except Exception as exc:
            errors.append(f"2captcha:{exc}")
            log.warning("2captcha_failed", run_id=run_id, error=str(exc))

    _failures[run_id] += 1
    if _failures[run_id] >= 2:
        raise CaptchaEscalateError(f"2 consecutive CAPTCHA failures for {run_id}: {errors}")
    raise RuntimeError(f"CAPTCHA solve failed: {errors}")

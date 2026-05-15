"""
Gmail API helper (OAuth refresh token in Keychain). Full flow: BUILD.md Task 0.5.

Importing this module must not require credentials at import time — CI and cold starts rely on that.
"""

from __future__ import annotations

import json
from typing import Any

# Lazy surface for `from agents.tools.gmail import get_service` (Phase 0 exit criteria).
_service_cache: Any | None = None


def get_service() -> Any:
    """
    Return a Gmail API resource object (`googleapiclient.discovery.build`).

    Raises ``RuntimeError`` until OAuth has been completed (`make oauth-gmail`, Task 0.5).
    """
    global _service_cache
    if _service_cache is not None:
        return _service_cache

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    from agents.tools import keychain as kc

    raw = kc.get_secret("gmail", "oauth_token_json")
    if not raw:
        raise RuntimeError(
            "Gmail OAuth token not in Keychain. See docs/GMAIL_SETUP.md; run `make oauth-gmail`."
        )

    creds = Credentials.from_authorized_user_info(
        json.loads(raw),
        scopes=[
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
        ],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        kc.set_secret("gmail", creds.to_json(), "oauth_token_json")

    _service_cache = build("gmail", "v1", credentials=creds, cache_discovery=False)
    return _service_cache

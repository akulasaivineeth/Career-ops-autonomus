"""
Gmail API helper (OAuth refresh token in Keychain). BUILD.md Task 0.5.

Scopes: ``gmail.readonly`` + ``gmail.modify`` only (no send, no full-mail scope).
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path
from typing import Any

SCOPES: tuple[str, ...] = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
)

_service_cache: Any | None = None


def _default_client_secret_path() -> Path:
    env = os.environ.get("GMAIL_CREDENTIALS_PATH")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".career-ops" / "gmail-credentials.json"


def get_service() -> Any:
    """
    Return a Gmail API resource (``googleapiclient.discovery.build``).

    Raises ``RuntimeError`` until OAuth has been completed (``make oauth-gmail``).
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
        scopes=list(SCOPES),
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        kc.set_secret("gmail", creds.to_json(), "oauth_token_json")

    _service_cache = build("gmail", "v1", credentials=creds, cache_discovery=False)
    return _service_cache


def search(service: Any, query: str, *, max_results: int = 25) -> list[dict[str, Any]]:
    """List message metadata matching Gmail ``q`` syntax."""
    resp = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    return list(resp.get("messages", []))


def _decode_part_body(part: dict[str, Any]) -> str:
    data = part.get("body", {}).get("data")
    if not data:
        return ""
    raw = base64.urlsafe_b64decode(data.encode("ascii")).decode("utf-8", errors="replace")
    return raw


def _walk_parts(payload: dict[str, Any], out: list[str]) -> None:
    if "parts" in payload:
        for p in payload["parts"]:
            _walk_parts(p, out)
    mime = payload.get("mimeType", "")
    if mime in {"text/plain", "text/html"}:
        out.append(_decode_part_body(payload))


def get_body_text(service: Any, msg_id: str) -> str:
    """Return best-effort plain/HTML body text for a message id."""
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    chunks: list[str] = []
    _walk_parts(msg.get("payload", {}), chunks)
    return "\n".join(c for c in chunks if c).strip()


def mark_read(service: Any, msg_id: str) -> None:
    """Remove UNREAD label (read receipt for automation)."""
    service.users().messages().modify(
        userId="me",
        id=msg_id,
        body={"removeLabelIds": ["UNREAD"]},
    ).execute()


_CODE_RE = re.compile(r"\b(\d{4,8})\b")


def get_verification_code(
    service: Any,
    sender_domain: str,
    *,
    poll_seconds: int = 120,
    interval: int = 5,
    newer_than: str = "1d",
) -> str | None:
    """
    Poll inbox for a numeric verification code from ``sender_domain``.

    ``newer_than`` is passed to Gmail ``q`` (e.g. ``1d``, ``7d``), not raw seconds.
    """
    deadline = time.monotonic() + poll_seconds
    query = f"from:{sender_domain} newer_than:{newer_than}"
    while time.monotonic() < deadline:
        for meta in search(service, query, max_results=5):
            mid = meta["id"]
            body = get_body_text(service, mid)
            if m := _CODE_RE.search(body):
                return m.group(1)
        time.sleep(interval)
    return None


def run_oauth_flow() -> None:
    """Run OAuth interactively; stores refresh token JSON in Keychain (gmail / oauth_token_json)."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    from agents.tools import keychain as kc

    client_path = _default_client_secret_path()
    if not client_path.is_file():
        raise SystemExit(
            f"Missing Gmail OAuth client JSON at {client_path}. "
            "See BUILD.md Task −1.6 / docs/GMAIL_SETUP.md."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(client_path), scopes=list(SCOPES))
    creds = flow.run_local_server(port=0, prompt="consent")
    kc.set_secret("gmail", creds.to_json(), "oauth_token_json")
    print("Stored Gmail OAuth token in Keychain (careerops.gmail / oauth_token_json).")


if __name__ == "__main__":
    run_oauth_flow()

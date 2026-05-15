"""WhatsApp Cloud API client (Meta direct) — BUILD.md Task 1.5, arch.G.2."""

from __future__ import annotations

import os
from pathlib import Path

import httpx
import structlog

log = structlog.get_logger(__name__)

GRAPH_API = "https://graph.facebook.com/v21.0"


def _phone_number_id() -> str:
    val = os.environ.get("WA_PHONE_NUMBER_ID", "")
    if not val:
        raise RuntimeError("WA_PHONE_NUMBER_ID env var not set. See docs/WHATSAPP_SETUP.md.")
    return val


def _to_number() -> str:
    val = os.environ.get("WA_USER_NUMBER", "")
    if not val:
        raise RuntimeError("WA_USER_NUMBER env var not set. See docs/WHATSAPP_SETUP.md.")
    return val


def _token() -> str:
    from agents.tools.keychain import whatsapp_token

    tok = whatsapp_token()
    if not tok:
        raise RuntimeError(
            "WhatsApp token not in Keychain (careerops.whatsapp / access_token). "
            "See docs/WHATSAPP_SETUP.md."
        )
    return tok


def send_text(text: str) -> str:
    """Send a text message. Returns the WhatsApp message ID."""
    resp = httpx.post(
        f"{GRAPH_API}/{_phone_number_id()}/messages",
        headers={"Authorization": f"Bearer {_token()}"},
        json={
            "messaging_product": "whatsapp",
            "to": _to_number(),
            "type": "text",
            "text": {"body": text[:4096]},
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["messages"][0]["id"]


def send_image_with_caption(image_path: str, caption: str) -> str:
    """Upload image then send with caption. Returns message ID."""
    with open(image_path, "rb") as fh:
        media_resp = httpx.post(
            f"{GRAPH_API}/{_phone_number_id()}/media",
            headers={"Authorization": f"Bearer {_token()}"},
            data={"messaging_product": "whatsapp", "type": "image/png"},
            files={"file": (Path(image_path).name, fh, "image/png")},
            timeout=60,
        )
        media_resp.raise_for_status()
        media_id = media_resp.json()["id"]

    resp = httpx.post(
        f"{GRAPH_API}/{_phone_number_id()}/messages",
        headers={"Authorization": f"Bearer {_token()}"},
        json={
            "messaging_product": "whatsapp",
            "to": _to_number(),
            "type": "image",
            "image": {"id": media_id, "caption": caption[:1024]},
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["messages"][0]["id"]

"""
Anthropic Computer Use shim (claude-sonnet-4-5 ``computer_use_20250124`` tool).

Used as fallback when deterministic ATS adapters cannot parse the form (BUILD.md Task 1.6).
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_MAX_STEPS_PER_PAGE = 8


def run_computer_use_step(
    page: Any,
    instruction: str,
    screenshot_path: str,
    run_id: str,
) -> str:
    """
    Execute one vision-driven step on ``page`` using Anthropic Computer Use.

    Returns the model's action description string.
    """
    from agents.tools.keychain import claude_api_key

    key = claude_api_key()
    if not key:
        log.warning("computer_use_no_api_key")
        return "noop:no_api_key"

    import anthropic

    client = anthropic.Anthropic(api_key=key)

    # Encode screenshot
    shot = Path(screenshot_path)
    if not shot.exists():
        return "noop:no_screenshot"
    img_data = base64.standard_b64encode(shot.read_bytes()).decode()

    resp = client.beta.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        tools=[
            {
                "type": "computer_20250124",
                "name": "computer",
                "display_width_px": 1280,
                "display_height_px": 800,
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": img_data},
                    },
                    {"type": "text", "text": instruction},
                ],
            }
        ],
        betas=["computer-use-2024-10-22"],
    )

    # Parse first tool use block and execute on page
    for block in resp.content:
        if hasattr(block, "type") and block.type == "tool_use":
            action = block.input
            _execute_action(page, action)
            return str(action)

    text = " ".join(b.text for b in resp.content if hasattr(b, "text"))
    return text or "noop:no_action"


def _execute_action(page: Any, action: dict[str, Any]) -> None:
    """Translate a Computer Use action dict to a Playwright command."""
    kind = action.get("action")
    if kind == "screenshot":
        return
    if kind == "click":
        x, y = action.get("coordinate", [0, 0])
        page.mouse.click(x, y)
    elif kind == "type":
        text = action.get("text", "")
        page.keyboard.type(text)
    elif kind == "key":
        page.keyboard.press(action.get("key", ""))
    elif kind == "scroll":
        x, y = action.get("coordinate", [0, 0])
        dx, dy = action.get("delta", [0, 0])
        page.mouse.wheel(dx, dy)
    else:
        log.warning("computer_use_unknown_action", kind=kind)

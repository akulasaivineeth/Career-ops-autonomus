"""Greenhouse adapter — unit tests with mocked Playwright page (BUILD.md Task 1.4)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from agents.adapters.ats_greenhouse import GreenhouseAdapter, _try_fill


def _make_page(url: str = "https://boards.greenhouse.io/example/jobs/1") -> MagicMock:
    page = MagicMock()
    page.url = url
    return page


def _noop_approval(gate: str, shot: str, summary: str) -> str:
    return "approved"


def _noop_screenshot(label: str) -> str:
    return "/tmp/test.png"


def test_adapter_fills_personal_fields() -> None:
    page = _make_page()
    adapter = GreenhouseAdapter()
    adapter._load_profile = lambda: {  # type: ignore[method-assign]
        "identity": {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "phone": "555-0101",
        }
    }

    adapter._fill_personal(page, adapter._load_profile()["identity"])

    page.fill.assert_any_call("#first_name", "Jane")
    page.fill.assert_any_call("#last_name", "Doe")
    page.fill.assert_any_call("#email", "jane@example.com")
    page.fill.assert_any_call("#phone", "555-0101")


def test_adapter_never_clicks_submit_without_approval(tmp_path: Any) -> None:
    page = _make_page()
    adapter = GreenhouseAdapter()
    adapter._load_profile = lambda: {"identity": {}}  # type: ignore[method-assign]
    adapter._fill_personal = lambda *a, **k: None  # type: ignore[method-assign]
    adapter._upload_resume = lambda *a, **k: None  # type: ignore[method-assign]
    adapter._fill_cover = lambda *a, **k: None  # type: ignore[method-assign]
    adapter._handle_eeo = lambda *a, **k: None  # type: ignore[method-assign]

    def rejecting_callback(gate: str, shot: str, summary: str) -> str:
        return "rejected"

    result = adapter.run_sync(
        page,
        pdf_path=None,
        cover_path=None,
        run_id="test-r1",
        approval_callback=rejecting_callback,
        screenshot_fn=_noop_screenshot,
    )

    assert result.get("submitted") is False
    page.click.assert_not_called()


def test_try_fill_skips_empty_value() -> None:
    page = MagicMock()
    _try_fill(page, "#first_name", "")
    page.fill.assert_not_called()

"""Base ATS adapter interface (BUILD.md Task 1.4)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class ATSAdapter(ABC):
    """
    Abstract base for site-specific form drivers.

    Subclasses fill form fields from ``profile`` / PDF.  They must NEVER click
    the final submit button themselves; that is the harness's responsibility
    after ``approval_callback("final_submit", ...)`` returns ``"approved"``.
    """

    @abstractmethod
    def run_sync(
        self,
        page: Any,
        *,
        pdf_path: str | None,
        cover_path: str | None,
        run_id: str,
        approval_callback: Callable[[str, str, str], str],
        screenshot_fn: Callable[[str], str],
    ) -> dict[str, Any]:
        """
        Fill all form fields and await approval before submit.

        Returns ``{"submitted": bool, ...extra}``.
        """
        ...  # pragma: no cover

    def _load_profile(self) -> dict[str, Any]:
        try:
            from pathlib import Path

            import yaml  # type: ignore[import-untyped]

            path = Path(__file__).resolve().parents[2] / "config" / "profile.yml"
            return yaml.safe_load(path.read_text()) if path.exists() else {}
        except Exception:
            return {}

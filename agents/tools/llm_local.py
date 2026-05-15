"""Ollama local LLM shim (Qwen3/Phi-4) for cheap tasks (BUILD.md Task 3.2)."""

from __future__ import annotations

import structlog

log = structlog.get_logger(__name__)

_DEFAULT_MODEL = "qwen3:8b"
_CLASSIFIER_MODEL = "phi:3.8b"


def generate(prompt: str, *, model: str = _DEFAULT_MODEL) -> str:
    """Run a generation against local Ollama. Returns text."""
    try:
        import httpx

        resp = httpx.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as exc:
        log.warning("llm_local_failed", model=model, error=str(exc))
        return ""


def classify_email(body_text: str) -> str:
    """
    Classify email body as ``confirmation``, ``rejection``, or ``newsletter``.

    Uses local Phi-4 if available; falls back to keyword heuristic.
    """
    result = generate(
        f"Classify this email as exactly one of: confirmation, rejection, newsletter.\n"
        f"Reply with one word only.\n\nEMAIL:\n{body_text[:500]}",
        model=_CLASSIFIER_MODEL,
    )
    for label in ("confirmation", "rejection", "newsletter"):
        if label in result.lower():
            return label
    # Keyword fallback
    text_lower = body_text.lower()
    if any(w in text_lower for w in ("thank", "received", "submitted")):
        return "confirmation"
    if any(w in text_lower for w in ("not", "other candidates", "pursuing")):
        return "rejection"
    return "newsletter"


def extract_keywords(text: str, *, top_n: int = 20) -> list[str]:
    """Extract key technical terms from JD using local Qwen3."""
    result = generate(
        f"Extract the {top_n} most important technical keywords from this text.\n"
        f"Reply with a comma-separated list, no explanations.\n\nTEXT:\n{text[:1500]}",
    )
    return [kw.strip() for kw in result.split(",") if kw.strip()][:top_n]

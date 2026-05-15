"""Scorer worker — rates a JD 1-5 and picks a CV track (BUILD.md Task 1.2, arch.F.3)."""

from __future__ import annotations

import json
import re
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "scorer.md"
_REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"
_CV_DIR = Path(__file__).resolve().parents[2] / "cv"

VALID_TRACKS = {"DA", "MLE", "DE"}
SCORE_PASS = 4.5
SCORE_BORDERLINE = 4.0

# Kill-signal patterns: auto-reject regardless of score.
_KILL_PATTERNS = [
    re.compile(r"no\s+(?:visa|sponsorship|work\s+auth)", re.I),
    re.compile(r"us\s+citizen(?:ship)?\s+required", re.I),
    re.compile(r"security\s+clearance\s+required", re.I),
]


def _load_cv(track: str) -> str:
    path = _CV_DIR / f"{track.lower()}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _keyword_match(must_haves: list[str], cv_text: str) -> float:
    if not must_haves:
        return 1.0
    cv_lower = cv_text.lower()
    hits = sum(1 for kw in must_haves if kw.lower() in cv_lower)
    return hits / len(must_haves)


def _kill_signals(jd_text: str) -> list[str]:
    return [p.pattern for p in _KILL_PATTERNS if p.search(jd_text)]


def _next_report_number() -> str:
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(_REPORTS_DIR.glob("[0-9][0-9][0-9]-*.md"))
    nums = [int(p.stem.split("-")[0]) for p in existing if p.stem[0:3].isdigit()]
    return f"{(max(nums) + 1 if nums else 1):03d}"


def _write_report(run_id: str, result: dict[str, Any]) -> str:
    num = _next_report_number()
    slug = re.sub(r"[^a-z0-9]+", "-", result.get("track", "unknown").lower())
    date = datetime.now().strftime("%Y-%m-%d")
    name = f"{num}-{slug}-{date}.md"
    path = _REPORTS_DIR / name
    content = textwrap.dedent(f"""\
        # Score report — {name}

        **run_id:** {run_id}
        **track:** {result.get("track")}
        **score:** {result.get("score")}
        **status:** {result.get("status")}

        ## Rationale
        {result.get("rationale", "")}

        ## Kill signals
        {result.get("kill_signals", [])}

        ## Tailor keywords
        {result.get("tailor_keywords", [])}
    """)
    path.write_text(content, encoding="utf-8")
    return str(path)


def score_jd(
    jd_text: str,
    *,
    run_id: str = "local",
    anthropic_client: Any | None = None,
) -> dict[str, Any]:
    """
    Score a JD against all three CV tracks and return a structured dict.

    ``anthropic_client`` is injected in tests; production reads from Keychain.
    """
    from agents.tools.keychain import claude_api_key

    system = _PROMPT_PATH.read_text(encoding="utf-8")

    # Gather CV texts for keyword matching
    cv_texts = {t: _load_cv(t) for t in VALID_TRACKS}
    kill = _kill_signals(jd_text)

    # Pick the track with the highest simple keyword score as the default path.
    # Real semantic similarity requires Ollama (Task 3.3); use keyword-only until then.
    scores_by_track: dict[str, float] = {}
    for track, cv in cv_texts.items():
        must_haves = re.findall(r"\b[A-Z][a-zA-Z]+\b", jd_text)[:30]
        scores_by_track[track] = _keyword_match(must_haves, cv)
    best_track = max(scores_by_track, key=lambda t: scores_by_track[t])

    if anthropic_client is None:
        key = claude_api_key()
        if not key:
            log.warning("scorer_no_api_key_using_heuristic")
            # Heuristic fallback when no API key is available (CI / dry-run).
            composite = scores_by_track[best_track]
            heuristic_score = round(1.0 + composite * 4.0, 1)
            result: dict[str, Any] = {
                "track": best_track,
                "score": heuristic_score,
                "subscores": {
                    "keyword_match": scores_by_track[best_track],
                    "semantic_sim": 0.0,
                    "experience_fit": 0.5,
                },
                "dimensions": {},
                "rationale": "Heuristic scoring (no Anthropic key available).",
                "kill_signals": kill,
                "tailor_keywords": [],
                "status": (
                    "rejected_auto"
                    if kill or heuristic_score < SCORE_BORDERLINE
                    else "score_pass"
                    if heuristic_score >= SCORE_PASS
                    else "score_borderline"
                ),
            }
            result["report_path"] = _write_report(run_id, result)
            return result

        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatAnthropic(model="claude-sonnet-4-5", api_key=key, max_tokens=1024)
        anthropic_client = llm

    # Build prompt with CV summaries
    cv_summary = "\n".join(f"### {t}\n{cv_texts[t][:800]}" for t in VALID_TRACKS)
    user_msg = f"JD TEXT:\n{jd_text[:3000]}\n\n---\nCV TRACKS:\n{cv_summary}"

    from langchain_core.messages import HumanMessage, SystemMessage

    resp = anthropic_client.invoke([SystemMessage(content=system), HumanMessage(content=user_msg)])
    raw = resp.content if hasattr(resp, "content") else str(resp)

    # Extract JSON block from response
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        result = json.loads(m.group())
    else:
        result = {"track": best_track, "score": 3.0, "rationale": raw, "kill_signals": kill}

    result.setdefault("kill_signals", kill)
    if kill:
        result["status"] = "rejected_auto"
    else:
        sc = float(result.get("score", 0))
        result["status"] = (
            "rejected_auto"
            if sc < SCORE_BORDERLINE
            else "score_pass"
            if sc >= SCORE_PASS
            else "score_borderline"
        )

    result["report_path"] = _write_report(run_id, result)
    return result

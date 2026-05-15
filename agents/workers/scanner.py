"""Scanner worker — discovers new JDs from Greenhouse/Lever/Ashby APIs (BUILD.md Task 3.1)."""

from __future__ import annotations

import csv
import hashlib
import time
from pathlib import Path
from typing import Any

import httpx
import structlog

log = structlog.get_logger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_JDS_DIR = _REPO_ROOT / "jds"
_DATA_DIR = _REPO_ROOT / "data"
_PIPELINE_MD = _DATA_DIR / "pipeline.md"
_SCAN_HISTORY = _DATA_DIR / "scan-history.tsv"

MAX_NEW_PER_RUN = 200
BACKOFF_SECONDS = 3600  # 1 h backoff on 429


def _jd_hash(company: str, role: str, location: str) -> str:
    raw = f"{company.lower()}|{role.lower()}|{location.lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _load_seen() -> set[str]:
    if not _SCAN_HISTORY.exists():
        return set()
    with open(_SCAN_HISTORY, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return {row.get("hash", "") for row in reader if row.get("hash")}


def _record_seen(jd_hash: str, jd_id: str, title: str, company: str) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    header = not _SCAN_HISTORY.exists()
    with open(_SCAN_HISTORY, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        if header:
            writer.writerow(["hash", "jd_id", "title", "company", "scanned_at"])
        writer.writerow([jd_hash, jd_id, title, company, time.strftime("%Y-%m-%dT%H:%M:%S")])


def _append_pipeline(jd_id: str, url: str, title: str, company: str, source: str) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not _PIPELINE_MD.exists():
        _PIPELINE_MD.write_text(
            "# Pipeline\n\n| jd_id | title | company | source | status | url |\n"
            "|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )
    with open(_PIPELINE_MD, "a", encoding="utf-8") as f:
        f.write(f"| {jd_id} | {title} | {company} | {source} | queued | {url} |\n")


def scan_greenhouse(company_slugs: list[str], *, seen: set[str]) -> list[str]:
    """Fetch new JDs from Greenhouse public boards API."""
    new_ids: list[str] = []
    for slug in company_slugs:
        try:
            resp = httpx.get(
                f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
                timeout=15,
            )
            if resp.status_code == 429:
                log.warning("greenhouse_429", slug=slug)
                break
            resp.raise_for_status()
            for job in resp.json().get("jobs", []):
                h = _jd_hash(slug, job.get("title", ""), job.get("location", {}).get("name", ""))
                if h in seen:
                    continue
                jd_id = f"GH-{job['id']}"
                _write_jd(jd_id, job.get("content", ""), job.get("absolute_url", ""))
                _append_pipeline(
                    jd_id, job.get("absolute_url", ""), job.get("title", ""), slug, "greenhouse"
                )
                _record_seen(h, jd_id, job.get("title", ""), slug)
                seen.add(h)
                new_ids.append(jd_id)
                if len(new_ids) >= MAX_NEW_PER_RUN:
                    return new_ids
        except Exception as exc:
            log.error("greenhouse_scan_error", slug=slug, error=str(exc))
    return new_ids


def scan_lever(company_slugs: list[str], *, seen: set[str]) -> list[str]:
    """Fetch new JDs from Lever postings API."""
    new_ids: list[str] = []
    for slug in company_slugs:
        try:
            resp = httpx.get(
                f"https://api.lever.co/v0/postings/{slug}?mode=json",
                timeout=15,
            )
            if resp.status_code == 429:
                log.warning("lever_429", slug=slug)
                break
            resp.raise_for_status()
            for posting in resp.json():
                h = _jd_hash(
                    slug,
                    posting.get("text", ""),
                    posting.get("categories", {}).get("location", ""),
                )
                if h in seen:
                    continue
                jd_id = f"LV-{posting['id']}"
                content = posting.get("descriptionPlain", "") or posting.get("description", "")
                _write_jd(jd_id, content, posting.get("hostedUrl", ""))
                _append_pipeline(
                    jd_id, posting.get("hostedUrl", ""), posting.get("text", ""), slug, "lever"
                )
                _record_seen(h, jd_id, posting.get("text", ""), slug)
                seen.add(h)
                new_ids.append(jd_id)
                if len(new_ids) >= MAX_NEW_PER_RUN:
                    return new_ids
        except Exception as exc:
            log.error("lever_scan_error", slug=slug, error=str(exc))
    return new_ids


def _write_jd(jd_id: str, content: str, url: str) -> None:
    _JDS_DIR.mkdir(parents=True, exist_ok=True)
    path = _JDS_DIR / f"{jd_id}.txt"
    path.write_text(f"URL: {url}\n\n{content}", encoding="utf-8")


def scan_all(
    *,
    greenhouse_slugs: list[str] | None = None,
    lever_slugs: list[str] | None = None,
) -> dict[str, Any]:
    """Run all configured scanners and return a summary."""
    seen = _load_seen()
    new_ids: list[str] = []
    failed: list[str] = []

    if greenhouse_slugs:
        try:
            new_ids += scan_greenhouse(greenhouse_slugs, seen=seen)
        except Exception as exc:
            log.error("scanner_greenhouse_fatal", error=str(exc))
            failed.append("greenhouse")

    if lever_slugs:
        try:
            new_ids += scan_lever(lever_slugs, seen=seen)
        except Exception as exc:
            log.error("scanner_lever_fatal", error=str(exc))
            failed.append("lever")

    return {
        "new_jd_ids": new_ids,
        "skipped_duplicates": len(seen) - len(new_ids),
        "sources_failed": failed,
    }

"""nomic-embed-text embeddings via Ollama for semantic similarity (BUILD.md Task 3.3)."""

from __future__ import annotations

import math
import sqlite3
from pathlib import Path

import httpx
import structlog

log = structlog.get_logger(__name__)

_DB_PATH = Path(__file__).resolve().parents[2] / "db" / "careerops.db"
_EMBED_MODEL = "nomic-embed-text"
_DIM = 768


def embed_text(text: str) -> list[float]:
    """
    Embed ``text`` using Ollama ``nomic-embed-text``.

    Returns zero vector on failure (so callers can degrade gracefully).
    """
    try:
        resp = httpx.post(
            "http://localhost:11434/api/embeddings",
            json={"model": _EMBED_MODEL, "prompt": text[:4096]},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]
    except Exception as exc:
        log.warning("embed_text_failed", error=str(exc))
        return [0.0] * _DIM


def cosine_sim(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)  # noqa: B905 — vectors always same length by construction


def store_embedding(jd_id: str, embedding: list[float]) -> None:
    """Persist JD embedding blob to SQLite ``jd_embeddings`` table."""
    import struct

    blob = struct.pack(f"{len(embedding)}f", *embedding)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute(
        "INSERT OR REPLACE INTO jd_embeddings (jd_id, embedding) VALUES (?, ?)",
        (jd_id, blob),
    )
    conn.commit()
    conn.close()


def load_embedding(jd_id: str) -> list[float] | None:
    """Load a stored embedding from SQLite."""
    import struct

    if not _DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(_DB_PATH))
    row = conn.execute(
        "SELECT embedding FROM jd_embeddings WHERE jd_id = ?",
        (jd_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    n = len(row[0]) // 4
    return list(struct.unpack(f"{n}f", row[0]))

"""Embeddings tool tests — mocked Ollama (BUILD.md Task 3.3)."""

from __future__ import annotations

from unittest.mock import patch

from agents.tools import embeddings as emb_mod


def test_cosine_sim_identical() -> None:
    v = [1.0, 2.0, 3.0]
    assert abs(emb_mod.cosine_sim(v, v) - 1.0) < 1e-6


def test_cosine_sim_orthogonal() -> None:
    a = [1.0, 0.0, 0.0]
    b = [0.0, 1.0, 0.0]
    assert abs(emb_mod.cosine_sim(a, b)) < 1e-6


def test_cosine_sim_zero_vector() -> None:
    a = [0.0] * 768
    b = [1.0] * 768
    assert emb_mod.cosine_sim(a, b) == 0.0


def test_embed_text_fallback_on_ollama_unavailable() -> None:
    import agents.tools.embeddings as _emb

    with patch.object(_emb.httpx, "post", side_effect=OSError("connection refused")):
        vec = emb_mod.embed_text("hello world")
    assert len(vec) == 768
    assert all(v == 0.0 for v in vec)


def test_store_load_roundtrip(tmp_path, monkeypatch) -> None:
    db = tmp_path / "test.db"
    monkeypatch.setattr(emb_mod, "_DB_PATH", db)

    from db.migrate import apply_migrations

    apply_migrations(db)

    vec = [float(i % 10) / 10 for i in range(768)]
    emb_mod.store_embedding("JD-001", vec)
    loaded = emb_mod.load_embedding("JD-001")
    assert loaded is not None
    assert len(loaded) == 768
    assert abs(loaded[5] - vec[5]) < 1e-4

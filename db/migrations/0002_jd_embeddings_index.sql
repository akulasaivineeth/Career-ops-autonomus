-- Add a hash-based dedup index for JD embeddings (BUILD.md Task 3.3).
-- sqlite-vec KNN queries work directly on the jd_embeddings.embedding BLOB column.

CREATE INDEX IF NOT EXISTS idx_jd_embeddings_jd_id ON jd_embeddings (jd_id);

"""
ORCA RAG Embedder

Wraps a sentence-transformers embedding model for real semantic search,
used by nlp/rag/vector_store.py and nlp/rag/rag_pipeline.py.

Design goals (why this file looks defensive):
- `sentence-transformers` is already a declared dependency (see
  requirements.txt), but it has never actually been imported at runtime
  before this change. Loading it pulls in torch, which is a meaningfully
  larger runtime memory footprint than anything else in this service.
- The production backend currently runs on Render's free tier (512MB RAM).
  Loading the model there for the first time is an unknown until measured.
- Therefore this module is OFF by default (`ENABLE_VECTOR_RAG` env var),
  lazy (the model is never imported/loaded until the first real retrieval
  call, and only if enabled), and every failure mode (missing package,
  incompatible torch/transformers versions, out-of-memory, corrupt model
  cache, etc.) is caught and turned into "embeddings unavailable" rather
  than a crash or a raised exception. Callers (nlp/rag/rag_pipeline.py)
  MUST treat `None` as "fall back to the keyword retriever" so a
  misconfigured or resource-constrained deployment never breaks chat.

See `to_implement.md` for how to turn this on safely in production.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

logger = logging.getLogger("orca.rag.embedder")

ENABLE_VECTOR_RAG = os.getenv("ENABLE_VECTOR_RAG", "false").strip().lower() in (
    "1",
    "true",
    "yes",
)

# all-MiniLM-L6-v2: 384-dim, ~90MB, one of the smallest/fastest widely-used
# sentence-transformers models -- chosen specifically to minimize memory
# footprint for a resource-constrained deployment.
EMBEDDING_MODEL_NAME = os.getenv(
    "RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

_model = None
_model_load_failed = False


def _load_model():
    """
    Lazily import and construct the SentenceTransformer model exactly once.
    Returns None (and remembers the failure, so we never retry a doomed
    import on every request) if anything goes wrong.
    """
    global _model, _model_load_failed

    if _model is not None:
        return _model
    if _model_load_failed:
        return None

    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info("Loaded sentence-transformers model '%s'.", EMBEDDING_MODEL_NAME)
    except Exception:
        # Broad on purpose: import errors, version-mismatch errors raised
        # deep inside transformers/torch's own import chain, OOM errors,
        # and missing/corrupt model cache files can all land here.
        logger.exception(
            "Failed to load sentence-transformers model '%s'; "
            "semantic RAG retrieval is unavailable, falling back to keyword search.",
            EMBEDDING_MODEL_NAME,
        )
        _model_load_failed = True
        _model = None

    return _model


class MarineTextEmbedder:
    """
    Thin wrapper around a sentence-transformers model.

    Every public method returns `None` instead of raising when embeddings
    are disabled or unavailable for any reason -- callers must check for
    `None` and use the existing keyword-based retriever instead.
    """

    def __init__(self, enabled: Optional[bool] = None):
        self.enabled = ENABLE_VECTOR_RAG if enabled is None else enabled

    def is_available(self) -> bool:
        if not self.enabled:
            return False
        return _load_model() is not None

    def embed_query(self, text: str) -> Optional[List[float]]:
        if not self.enabled:
            return None
        model = _load_model()
        if model is None:
            return None
        try:
            vector = model.encode(text, normalize_embeddings=True)
            return vector.tolist()
        except Exception:
            logger.exception("Embedding a query failed; falling back to keyword search.")
            return None

    def embed_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        if not self.enabled:
            return None
        model = _load_model()
        if model is None:
            return None
        try:
            vectors = model.encode(texts, normalize_embeddings=True)
            return [v.tolist() for v in vectors]
        except Exception:
            logger.exception("Batch embedding failed.")
            return None

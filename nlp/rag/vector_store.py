"""
ORCA RAG Vector Store

A minimal, dependency-free (beyond numpy, already required by this
project) persisted vector index: a JSON file of
{source, text, section, chunk_id, embedding} records plus cosine
similarity search.

This deliberately avoids adding a full vector database (ChromaDB, FAISS,
etc.) -- the marine knowledge base this project ships (`data/knowledge/`)
is a handful of short text files producing on the order of a few dozen
chunks, so a linear cosine-similarity scan over an in-memory list is more
than fast enough and keeps the only new *runtime* dependency to the
embedding model itself (see embedder.py).

The index is built OFFLINE via `python -m nlp.rag.build_vector_index` and
committed/deployed as a static file -- the running server only ever reads
it, it never re-embeds the whole knowledge base on a request or at
startup.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger("orca.rag.vector_store")

DEFAULT_INDEX_PATH = Path(__file__).resolve().parent / ".vector_index" / "knowledge_index.json"


class VectorStore:
    """Loads a prebuilt embedding index and answers similarity queries."""

    def __init__(self, index_path: Optional[Path] = None):
        self.index_path = Path(index_path) if index_path else DEFAULT_INDEX_PATH
        self._records: List[Dict] = []
        self._matrix: Optional[np.ndarray] = None
        self._loaded = False
        self._load_failed = False
        self._pending_save_records: Optional[List[Dict]] = None

    def load(self) -> bool:
        """Load the index from disk once. Safe to call repeatedly."""
        if self._loaded:
            return True
        if self._load_failed:
            return False

        try:
            if not self.index_path.exists():
                logger.info(
                    "No vector index found at %s; semantic RAG retrieval is "
                    "unavailable until `python -m nlp.rag.build_vector_index` is run.",
                    self.index_path,
                )
                self._load_failed = True
                return False

            with open(self.index_path, "r", encoding="utf-8") as f:
                payload = json.load(f)

            records = payload.get("records", [])
            if not records:
                logger.warning("Vector index at %s has no records.", self.index_path)
                self._load_failed = True
                return False

            embeddings = np.array([r["embedding"] for r in records], dtype=np.float32)
            # Records are stored without the embedding for cheap iteration;
            # the embedding matrix is kept separately for vectorized search.
            self._records = [{k: v for k, v in r.items() if k != "embedding"} for r in records]
            self._matrix = embeddings
            self._loaded = True
            logger.info(
                "Loaded vector index with %d records from %s.",
                len(self._records),
                self.index_path,
            )
            return True
        except Exception:
            logger.exception("Failed to load vector index from %s.", self.index_path)
            self._load_failed = True
            return False

    def is_ready(self) -> bool:
        return self.load()

    def search(self, query_embedding: List[float], top_k: int = 3) -> List[Dict]:
        """
        Return up to `top_k` records most similar to `query_embedding`,
        each augmented with a `score` (cosine similarity, higher is
        better). Returns [] if the index isn't loaded/ready.
        """
        if not self.load() or self._matrix is None or len(self._records) == 0:
            return []

        try:
            query_vec = np.array(query_embedding, dtype=np.float32)
            query_norm = np.linalg.norm(query_vec)
            if query_norm == 0:
                return []

            matrix_norms = np.linalg.norm(self._matrix, axis=1)
            matrix_norms[matrix_norms == 0] = 1e-12  # avoid div-by-zero for any degenerate row

            similarities = (self._matrix @ query_vec) / (matrix_norms * query_norm)

            top_k = max(1, min(top_k, len(self._records)))
            top_indices = np.argsort(-similarities)[:top_k]

            results = []
            for idx in top_indices:
                record = dict(self._records[int(idx)])
                record["score"] = float(similarities[int(idx)])
                results.append(record)
            return results
        except Exception:
            logger.exception("Vector similarity search failed.")
            return []

    @staticmethod
    def build(records_with_embeddings: List[Dict]) -> "VectorStore":
        """
        Construct an in-memory VectorStore from a list of
        {source, text, section, chunk_id, embedding} dicts, ready to
        `.save()`. Used by the offline build script.
        """
        store = VectorStore()
        store._records = [
            {k: v for k, v in r.items() if k != "embedding"} for r in records_with_embeddings
        ]
        store._matrix = np.array(
            [r["embedding"] for r in records_with_embeddings], dtype=np.float32
        )
        store._loaded = True
        store._pending_save_records = records_with_embeddings
        return store

    def save(self, records_with_embeddings: Optional[List[Dict]] = None) -> None:
        """Persist the index to `self.index_path` as JSON."""
        records = records_with_embeddings or getattr(self, "_pending_save_records", None)
        if records is None:
            raise ValueError("No records with embeddings to save.")

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump({"records": records}, f)
        logger.info("Saved vector index with %d records to %s.", len(records), self.index_path)

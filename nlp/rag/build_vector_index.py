"""
ORCA RAG Vector Index Builder

Offline/manual step: loads the marine knowledge base, chunks it exactly
the way the live keyword retriever does, embeds every chunk with
sentence-transformers, and persists the result to
`nlp/rag/.vector_index/knowledge_index.json`.

This is intentionally NOT run automatically by the server at startup or
on any request -- embedding the whole knowledge base requires loading the
sentence-transformers model, and doing that unconditionally on every
deploy/boot would risk startup failures or memory pressure on a
resource-constrained host. Run this locally (or as a one-off Render job)
whenever the knowledge base changes, then commit/redeploy the resulting
index file.

Usage:
    python -m nlp.rag.build_vector_index
    python -m nlp.rag.build_vector_index --knowledge-path data/knowledge
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("orca.rag.build_vector_index")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--knowledge-path",
        default="data/knowledge",
        help="Folder of .txt/.md knowledge documents to index (default: data/knowledge)",
    )
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--chunk-overlap", type=int, default=50)
    args = parser.parse_args()

    # Force-enable the embedder for the duration of this script regardless
    # of the ENABLE_VECTOR_RAG environment variable -- building the index
    # is exactly the one place we *want* to load the model unconditionally.
    from nlp.rag.embedder import MarineTextEmbedder
    from nlp.rag.document_loader import load_documents, chunk_documents
    from nlp.rag.vector_store import VectorStore

    embedder = MarineTextEmbedder(enabled=True)
    if not embedder.is_available():
        logger.error(
            "sentence-transformers could not be loaded in this environment. "
            "Install/upgrade it here (see requirements.txt) before building the index. "
            "The existing index (if any) was left untouched."
        )
        return 1

    documents = load_documents(args.knowledge_path)
    if not documents:
        logger.error("No documents found under %s.", args.knowledge_path)
        return 1

    chunks = chunk_documents(
        documents=documents, chunk_size=args.chunk_size, overlap=args.chunk_overlap
    )
    if not chunks:
        logger.error("Documents were loaded but produced zero chunks.")
        return 1

    logger.info("Embedding %d chunks from %d documents...", len(chunks), len(documents))
    texts = [c["text"] for c in chunks]
    embeddings = embedder.embed_batch(texts)
    if embeddings is None:
        logger.error("Embedding failed; index was not written.")
        return 1

    records = []
    for chunk, embedding in zip(chunks, embeddings):
        records.append(
            {
                "source": chunk["source"],
                "text": chunk["text"],
                "section": chunk.get("section"),
                "chunk_id": chunk.get("chunk_id"),
                "embedding": embedding,
            }
        )

    store = VectorStore()
    store.save(records)
    logger.info(
        "Done. Wrote %d embedded chunks to %s. "
        "Set ENABLE_VECTOR_RAG=true to use this index at runtime.",
        len(records),
        store.index_path,
    )
    return 0


if __name__ == "__main__":
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    raise SystemExit(main())

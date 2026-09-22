"""
ORCA RAG Pipeline

Loads marine knowledge documents, splits them into chunks,
retrieves relevant chunks, and formats the final context.

Retrieval tries real semantic (embedding-based) search first via
nlp/rag/vector_store.py, and transparently falls back to the original
keyword-based retriever whenever semantic search is disabled, its index
hasn't been built yet, or anything about it fails -- see
nlp/rag/embedder.py for why that fallback exists and is unconditional.
"""

import logging
from pathlib import Path

from nlp.rag.document_loader import (
    load_documents,
    chunk_documents,
)
from nlp.rag.retriever import retrieve_documents
from nlp.rag.embedder import MarineTextEmbedder
from nlp.rag.vector_store import VectorStore

logger = logging.getLogger("orca.rag.pipeline")

DEFAULT_KNOWLEDGE_PATH = Path("data/knowledge")

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50

_embedder = MarineTextEmbedder()
_vector_store = VectorStore()


def _try_semantic_retrieval(query: str, top_k: int):
    """
    Returns (True, results) if semantic retrieval actually ran (results may
    legitimately be an empty list), or (False, []) if it was skipped for
    any reason -- callers should fall back to the keyword retriever only in
    the latter case.
    """
    try:
        if not _embedder.is_available() or not _vector_store.is_ready():
            return False, []

        query_vector = _embedder.embed_query(query)
        if query_vector is None:
            return False, []

        return True, _vector_store.search(query_vector, top_k=top_k)
    except Exception:
        logger.exception(
            "Semantic RAG retrieval failed unexpectedly; falling back to keyword search."
        )
        return False, []


def format_document_context(
    document: dict,
) -> str:
    """
    Format one retrieved chunk into clean factual text for LLM/NLP synthesis.
    Does NOT output internal chunk IDs or raw debug headers.
    """
    text = document.get("text", "").strip()
    return text


def get_relevant_context(
    query: str,
    knowledge_path: str = str(DEFAULT_KNOWLEDGE_PATH),
    top_k: int = 3,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> dict:
    """
    Load knowledge documents, split them into chunks,
    and retrieve the most relevant chunks.

    Returns:
        {
            "query": str,
            "documents": list,
            "context": str,
        }

    The original output structure is preserved.
    """

    if not isinstance(query, str):
        raise TypeError("query must be a string")

    if not isinstance(top_k, int):
        raise TypeError("top_k must be an integer")

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than zero"
        )

    if not isinstance(chunk_size, int):
        raise TypeError(
            "chunk_size must be an integer"
        )

    if not isinstance(chunk_overlap, int):
        raise TypeError(
            "chunk_overlap must be an integer"
        )

    if not query.strip():
        return {
            "query": query,
            "documents": [],
            "context": "",
        }

    used_semantic, relevant_documents = _try_semantic_retrieval(query, top_k)

    if not used_semantic:
        documents = load_documents(knowledge_path)

        chunks = chunk_documents(
            documents=documents,
            chunk_size=chunk_size,
            overlap=chunk_overlap,
        )

        relevant_documents = retrieve_documents(
            query=query,
            documents=chunks,
            top_k=top_k,
        )

    if not relevant_documents:
        return {
            "query": query,
            "documents": [],
            "context": "",
        }

    context_parts = []

    for index, document in enumerate(
        relevant_documents,
        start=1,
    ):
        context_parts.append(
            format_document_context(
                document=document,
            )
        )

    context = "\n\n".join(context_parts)

    return {
        "query": query,
        "documents": relevant_documents,
        "context": context,
    }
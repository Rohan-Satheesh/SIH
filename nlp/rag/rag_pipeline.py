"""
ORCA RAG Pipeline

Loads marine knowledge documents, splits them into chunks,
retrieves relevant chunks, and formats the final context.
"""

from pathlib import Path

from nlp.rag.document_loader import (
    load_documents,
    chunk_documents,
)
from nlp.rag.retriever import retrieve_documents


DEFAULT_KNOWLEDGE_PATH = Path("data/knowledge")

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50


def format_document_context(
    document: dict,
    document_number: int = 1,
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
                document_number=index,
            )
        )

    context = "\n\n".join(context_parts)

    return {
        "query": query,
        "documents": relevant_documents,
        "context": context,
    }
"""
ORCA RAG Retriever

Retrieves relevant documents using lightweight keyword-based scoring.

Features:
- Text normalization
- Stop-word removal
- Hyphen and underscore normalization
- Source filename matching
- Exact phrase matching
- Relevance scoring
- Empty-document protection
- Deterministic ranking
"""

import re


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "which",
    "with",
    "you",
    "your",
}


def normalize_text(text: str) -> str:
    """
    Normalize text for matching.

    Examples:
        "Wave-height" -> "wave height"
        "sea_surface_temperature" -> "sea surface temperature"
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    text = text.lower()

    text = text.replace("-", " ")
    text = text.replace("_", " ")

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


def tokenize(text: str) -> set[str]:
    """
    Convert text into normalized meaningful words.
    """

    normalized_text = normalize_text(text)

    words = normalized_text.split()

    return {
        word
        for word in words
        if word not in STOP_WORDS
    }


def calculate_relevance(
    query: str,
    document_text: str,
) -> int:
    """
    Calculate the number of shared meaningful words.
    """

    if not isinstance(query, str):
        raise TypeError("query must be a string")

    if not isinstance(document_text, str):
        raise TypeError(
            "document_text must be a string"
        )

    query_words = tokenize(query)
    document_words = tokenize(document_text)

    return len(
        query_words.intersection(document_words)
    )


def _contains_exact_phrase(
    query: str,
    document_text: str,
) -> bool:
    """
    Check whether the normalized query appears
    as an exact phrase inside the document.
    """

    normalized_query = normalize_text(query)
    normalized_document = normalize_text(document_text)

    if not normalized_query:
        return False

    return normalized_query in normalized_document


def calculate_document_score(
    query: str,
    source: str,
    document_text: str,
) -> float:
    """
    Calculate document relevance.

    Score components:

    - Shared meaningful words
    - Query coverage
    - Source filename matches
    - Exact phrase bonus
    """

    if not isinstance(query, str):
        raise TypeError("query must be a string")

    if not isinstance(source, str):
        raise TypeError("source must be a string")

    if not isinstance(document_text, str):
        raise TypeError(
            "document_text must be a string"
        )

    query_words = tokenize(query)
    document_words = tokenize(document_text)
    source_words = tokenize(source)

    if not query_words or not document_words:
        return 0.0

    shared_words = query_words.intersection(
        document_words
    )

    shared_count = len(shared_words)

    if shared_count == 0:
        return 0.0

    query_coverage = (
        shared_count / len(query_words)
    )

    source_matches = len(
        query_words.intersection(source_words)
    )

    source_boost = source_matches * 0.5

    phrase_bonus = 1.0 if _contains_exact_phrase(
        query,
        document_text,
    ) else 0.0

    score = (
        shared_count
        + query_coverage
        + source_boost
        + phrase_bonus
    )

    return round(score, 4)


def retrieve_documents(
    query: str,
    documents: list[dict],
    top_k: int = 3,
) -> list[dict]:
    """
    Return the most relevant documents.

    Required document structure:

        {
            "source": str,
            "text": str
        }

    Returned structure:

        {
            "source": str,
            "text": str,
            "score": float
        }
    """

    if not isinstance(query, str):
        raise TypeError("query must be a string")

    if not isinstance(documents, list):
        raise TypeError(
            "documents must be a list"
        )

    if not isinstance(top_k, int):
        raise TypeError(
            "top_k must be an integer"
        )

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than zero"
        )

    if not query.strip():
        return []

    scored_documents = []

    for document in documents:
        if not isinstance(document, dict):
            raise TypeError(
                "each document must be a dictionary"
            )

        if (
            "source" not in document
            or "text" not in document
        ):
            raise ValueError(
                "each document must contain source and text"
            )

        source = document["source"]
        text = document["text"]

        if not isinstance(source, str):
            raise TypeError(
                "document source must be a string"
            )

        if not isinstance(text, str):
            raise TypeError(
                "document text must be a string"
            )

        if not text.strip():
            continue

        score = calculate_document_score(
            query=query,
            source=source,
            document_text=text,
        )

        # Relevance filtering:
        # Documents with no meaningful matching words
        # are not returned.
        if score <= 0:
            continue

        result_document = dict(document)
        result_document["score"] = score

        scored_documents.append(
            result_document
        )

    scored_documents.sort(
        key=lambda item: (
            -item["score"],
            item["source"].lower(),
        )
    )

    return scored_documents[:top_k]
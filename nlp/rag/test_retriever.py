import pytest

from nlp.rag.retriever import (
    tokenize,
    calculate_relevance,
    calculate_document_score,
    retrieve_documents,
)


def test_tokenize():
    result = tokenize(
        "Sea Safety, Sea Weather!"
    )

    assert result == {
        "sea",
        "safety",
        "weather",
    }


def test_calculate_relevance():
    score = calculate_relevance(
        "sea safety",
        "Sea safety is important for fishermen",
    )

    assert score == 2


def test_retrieve_documents():
    documents = [
        {
            "source": "safety.txt",
            "text": (
                "Sea safety and wave height information"
            ),
        },
        {
            "source": "fishing.txt",
            "text": (
                "Fish locations and fishing zones"
            ),
        },
        {
            "source": "weather.txt",
            "text": (
                "Weather and wind speed information"
            ),
        },
    ]

    result = retrieve_documents(
        "wave height safety",
        documents,
        top_k=2,
    )

    assert len(result) == 1
    assert result[0]["source"] == "safety.txt"
    assert result[0]["score"] > 0


def test_empty_query():
    documents = [
        {
            "source": "safety.txt",
            "text": "Sea safety information",
        }
    ]

    result = retrieve_documents(
        "",
        documents,
    )

    assert result == []


def test_invalid_query():
    with pytest.raises(TypeError):
        retrieve_documents(
            123,
            [],
        )


def test_invalid_top_k():
    with pytest.raises(ValueError):
        retrieve_documents(
            "safety",
            [],
            top_k=0,
        )


def test_missing_document_field():
    documents = [
        {
            "source": "broken.txt",
        }
    ]

    with pytest.raises(ValueError):
        retrieve_documents(
            "safety",
            documents,
        )


def test_unrelated_query_returns_no_documents():
    documents = [
        {
            "source": "safety.txt",
            "text": (
                "Wear life jackets during dangerous weather."
            ),
        },
        {
            "source": "fishing.txt",
            "text": (
                "Potential Fishing Zones help fishermen."
            ),
        },
    ]

    result = retrieve_documents(
        "quantum mechanics and particle physics",
        documents,
    )

    assert result == []


def test_hyphenated_terms_are_normalized():
    result = tokenize(
        "Sea-surface-temperature and wave-height"
    )

    assert result == {
        "sea",
        "surface",
        "temperature",
        "wave",
        "height",
    }


def test_exact_phrase_gets_relevance_score():
    score = calculate_document_score(
        query="wave height",
        source="marine_safety.txt",
        document_text=(
            "Check wave height before sailing."
        ),
    )

    assert score > 0
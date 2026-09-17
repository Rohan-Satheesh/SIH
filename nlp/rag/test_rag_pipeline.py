import pytest

from nlp.rag.rag_pipeline import get_relevant_context


def test_safety_context():
    result = get_relevant_context(
        "How can fishermen stay safe during high waves?"
    )

    assert result["query"] == (
        "How can fishermen stay safe during high waves?"
    )

    assert len(result["documents"]) > 0
    assert "marine_safety.txt" in result["context"]
    assert "life jackets" in result["context"]


def test_pfz_context():
    result = get_relevant_context(
        "What is PFZ?"
    )

    assert len(result["documents"]) > 0
    assert "fishing_zones.txt" in result["context"]
    assert "Potential Fishing Zones" in result["context"]


def test_marine_terms_context():
    result = get_relevant_context(
        "What does IMBL mean?"
    )

    assert len(result["documents"]) > 0
    assert "marine_terms.txt" in result["context"]
    assert "International Maritime Boundary Line" in result["context"]


def test_empty_query():
    result = get_relevant_context("")

    assert result["documents"] == []
    assert result["context"] == ""


def test_invalid_query():
    with pytest.raises(TypeError):
        get_relevant_context(123)


def test_custom_top_k():
    result = get_relevant_context(
        "wind speed and wave height",
        top_k=1,
    )

    assert len(result["documents"]) <= 1
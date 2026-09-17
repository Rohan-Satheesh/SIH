import pytest

from nlp.templates.response_templates import (
    create_response,
    safety_response,
    pfz_response,
    general_response,
)


def test_create_response():
    result = create_response(
        "safety_check",
        "Check the weather before going to sea.",
        "EN",
    )

    assert result == {
        "intent": "SAFETY_CHECK",
        "language": "en",
        "answer": "Check the weather before going to sea.",
    }


def test_safety_response():
    result = safety_response(
        "Avoid going to sea during a cyclone."
    )

    assert result["intent"] == "SAFETY_CHECK"
    assert result["priority"] == "high"


def test_pfz_response():
    result = pfz_response(
        "PFZs indicate areas where fish may be more abundant."
    )

    assert result["intent"] == "PFZ_LOCATION"
    assert result["priority"] == "normal"


def test_general_response():
    result = general_response(
        "Hello fisherman!"
    )

    assert result["intent"] == "GENERAL_KNOWLEDGE"


def test_empty_intent():
    with pytest.raises(ValueError):
        create_response(
            "",
            "Some answer",
        )


def test_empty_answer():
    with pytest.raises(ValueError):
        create_response(
            "SAFETY_CHECK",
            "",
        )


def test_invalid_types():
    with pytest.raises(TypeError):
        create_response(
            123,
            "Some answer",
        )
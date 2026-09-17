"""
ORCA Response Templates

Creates consistent responses for common ORCA intents.
"""


def create_response(
    intent: str,
    answer: str,
    language: str = "en",
) -> dict:
    """
    Create a structured response.

    Returns:
        {
            "intent": str,
            "language": str,
            "answer": str,
        }
    """

    if not isinstance(intent, str):
        raise TypeError("intent must be a string")

    if not isinstance(answer, str):
        raise TypeError("answer must be a string")

    if not isinstance(language, str):
        raise TypeError("language must be a string")

    if not intent.strip():
        raise ValueError("intent cannot be empty")

    if not answer.strip():
        raise ValueError("answer cannot be empty")

    if not language.strip():
        raise ValueError("language cannot be empty")

    return {
        "intent": intent.strip().upper(),
        "language": language.strip().lower(),
        "answer": answer.strip(),
    }


def safety_response(answer: str, language: str = "en") -> dict:
    """
    Format a marine safety response.
    """

    result = create_response(
        intent="SAFETY_CHECK",
        answer=answer,
        language=language,
    )

    result["priority"] = "high"

    return result


def pfz_response(answer: str, language: str = "en") -> dict:
    """
    Format a Potential Fishing Zone response.
    """

    result = create_response(
        intent="PFZ_LOCATION",
        answer=answer,
        language=language,
    )

    result["priority"] = "normal"

    return result


def general_response(answer: str, language: str = "en") -> dict:
    """
    Format a general knowledge response.
    """

    result = create_response(
        intent="GENERAL_KNOWLEDGE",
        answer=answer,
        language=language,
    )

    result["priority"] = "normal"

    return result
"""
ORCA Text-to-Speech Interface

Provides a safe interface for converting text into speech.
The current version uses a placeholder implementation.
"""


SUPPORTED_VOICE_LANGUAGES = {
    "en",
    "ml",
    "hi",
    "ta",
    "te",
    "kn",
    "bn",
    "mr",
    "gu",
    "or",
    "pa",
}


def synthesize_speech(
    text: str,
    language: str = "en",
) -> dict:
    """
    Convert text into speech.

    Current version:
    Returns a safe placeholder response until a real
    text-to-speech engine is integrated.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not isinstance(language, str):
        raise TypeError("language must be a string")

    text = text.strip()
    language = language.strip().lower()

    if not text:
        raise ValueError("text cannot be empty")

    if language not in SUPPORTED_VOICE_LANGUAGES:
        raise ValueError(
            f"Unsupported voice language: {language}"
        )

    return {
        "text": text,
        "language": language,
        "audio_path": None,
        "success": False,
        "fallback_used": True,
        "message": (
            "Text-to-speech engine is not integrated yet."
        ),
    }


def is_supported_voice_language(language: str) -> bool:
    """
    Check whether a voice language is supported.
    """

    if not isinstance(language, str):
        return False

    return (
        language.strip().lower()
        in SUPPORTED_VOICE_LANGUAGES
    )
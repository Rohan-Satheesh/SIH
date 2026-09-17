"""
ORCA Speech-to-Text Interface

Provides a safe interface for converting speech into text.
The current version uses a placeholder implementation.
"""


SUPPORTED_AUDIO_FORMATS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".ogg",
}


def transcribe_audio(audio_path: str) -> dict:
    """
    Convert an audio file into text.

    Current version:
    Returns a safe placeholder response until a real
    speech-recognition model is integrated.
    """

    if not isinstance(audio_path, str):
        raise TypeError("audio_path must be a string")

    audio_path = audio_path.strip()

    if not audio_path:
        raise ValueError("audio_path cannot be empty")

    return {
        "text": "",
        "language": None,
        "confidence": 0.0,
        "success": False,
        "fallback_used": True,
        "message": (
            "Speech-to-text engine is not integrated yet."
        ),
    }


def is_supported_audio_format(audio_path: str) -> bool:
    """
    Check whether an audio file format is supported.
    """

    if not isinstance(audio_path, str):
        return False

    audio_path = audio_path.lower().strip()

    return any(
        audio_path.endswith(extension)
        for extension in SUPPORTED_AUDIO_FORMATS
    )
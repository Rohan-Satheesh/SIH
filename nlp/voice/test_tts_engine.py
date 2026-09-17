import pytest

from nlp.voice.tts_engine import (
    synthesize_speech,
    is_supported_voice_language,
)


def test_synthesize_speech():
    result = synthesize_speech(
        "Check the weather before going to sea."
    )

    assert result["text"] == (
        "Check the weather before going to sea."
    )
    assert result["language"] == "en"
    assert result["success"] is False
    assert result["fallback_used"] is True


def test_supported_language():
    assert is_supported_voice_language("en") is True
    assert is_supported_voice_language("ml") is True
    assert is_supported_voice_language("xyz") is False


def test_case_insensitive_language():
    assert is_supported_voice_language("ML") is True


def test_invalid_text():
    with pytest.raises(TypeError):
        synthesize_speech(123)


def test_empty_text():
    with pytest.raises(ValueError):
        synthesize_speech("")


def test_invalid_language():
    with pytest.raises(ValueError):
        synthesize_speech(
            "Hello",
            "xyz",
        )


def test_invalid_language_type():
    with pytest.raises(TypeError):
        synthesize_speech(
            "Hello",
            123,
        )
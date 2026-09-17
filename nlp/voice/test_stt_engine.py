import pytest

from nlp.voice.stt_engine import (
    transcribe_audio,
    is_supported_audio_format,
)


def test_transcribe_audio():
    result = transcribe_audio("sample.wav")

    assert result["text"] == ""
    assert result["success"] is False
    assert result["fallback_used"] is True


def test_audio_format():
    assert is_supported_audio_format("sample.wav") is True
    assert is_supported_audio_format("sample.mp3") is True
    assert is_supported_audio_format("sample.txt") is False


def test_audio_format_case_insensitive():
    assert is_supported_audio_format("SAMPLE.WAV") is True


def test_invalid_audio_path():
    with pytest.raises(TypeError):
        transcribe_audio(123)


def test_empty_audio_path():
    with pytest.raises(ValueError):
        transcribe_audio("")


def test_invalid_format_input():
    assert is_supported_audio_format(123) is False
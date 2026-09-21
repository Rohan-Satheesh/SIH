import pytest

import nlp.translation.translator as translator_module
from nlp.translation.translator import (
    SUPPORTED_LANGUAGES,
    is_supported_language,
    repair_mojibake,
    translate_response,
    translate_text,
    translate_to_english,
)


def test_english_to_english():
    result = translate_text(
        "Hello fisherman",
        "en",
        "en",
    )

    assert result["text"] == "Hello fisherman"
    assert result["translated"] is False
    assert result["fallback_used"] is True
    assert result["source_language"] == "en"
    assert result["target_language"] == "en"


def test_same_language():
    result = translate_text(
        "മത്സ്യബന്ധനം",
        "ml",
        "ml",
    )

    assert result["text"] == "മത്സ്യബന്ധനം"
    assert result["translated"] is False
    assert result["fallback_used"] is False
    assert result["source_language"] == "ml"
    assert result["target_language"] == "ml"


def test_fallback_translation(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    result = translate_text(
        "മത്സ്യബന്ധനം",
        "ml",
        "en",
    )

    assert result["fallback_used"] is True
    assert result["source_language"] == "ml"
    assert result["target_language"] == "en"
    assert result["text"] == "മത്സ്യബന്ധനം"


def test_supported_language():
    assert is_supported_language("ml") is True
    assert is_supported_language("en") is True
    assert is_supported_language("hi") is True
    assert is_supported_language("ta") is True
    assert is_supported_language("te") is True
    assert is_supported_language("bn") is True
    assert is_supported_language("mr") is True
    assert is_supported_language("gu") is True
    assert is_supported_language("kn") is True
    assert is_supported_language("or") is True
    assert is_supported_language("xyz") is False


def test_supported_language_is_case_insensitive():
    assert is_supported_language("EN") is True
    assert is_supported_language("Hi") is True
    assert is_supported_language("ML") is True


def test_supported_language_invalid_input():
    assert is_supported_language(123) is False
    assert is_supported_language(None) is False


def test_all_ten_languages_are_registered():
    expected_languages = {
        "en",
        "hi",
        "ta",
        "te",
        "bn",
        "mr",
        "gu",
        "kn",
        "ml",
        "or",
    }

    assert set(SUPPORTED_LANGUAGES.keys()) == expected_languages


def test_invalid_language():
    with pytest.raises(ValueError):
        translate_text(
            "hello",
            "xyz",
            "en",
        )


def test_invalid_target_language():
    with pytest.raises(ValueError):
        translate_text(
            "hello",
            "en",
            "xyz",
        )


def test_invalid_text():
    with pytest.raises(TypeError):
        translate_text(
            123,
            "en",
            "ml",
        )


def test_empty_text():
    with pytest.raises(ValueError):
        translate_text(
            "",
            "en",
            "ml",
        )


def test_whitespace_only_text():
    with pytest.raises(ValueError):
        translate_text(
            "   ",
            "en",
            "ml",
        )


def test_hindi_translation_to_english():
    result = translate_text(
        "तेज़ हवा",
        "hi",
        "en",
    )

    assert result["text"] == "strong winds"
    assert result["translated"] is True
    assert result["fallback_used"] is False


def test_tamil_translation_to_english():
    result = translate_text(
        "பலத்த காற்று",
        "ta",
        "en",
    )

    assert result["text"] == "strong winds"
    assert result["translated"] is True
    assert result["fallback_used"] is False


def test_repair_hindi_mojibake():
    corrupted = "à¤¹à¤µà¤¾"
    repaired = repair_mojibake(corrupted)

    assert repaired == "हवा"


def test_repair_tamil_mojibake():
    corrupted = "à®•à®Ÿà®²à¯"
    repaired = repair_mojibake(corrupted)

    # Some incomplete mojibake strings cannot be repaired safely.
    # The function must not crash or return another invalid object.
    assert isinstance(repaired, str)


def test_normal_text_is_unchanged():
    text = "Strong winds are expected."

    assert repair_mojibake(text) == text


def test_unicode_text_is_unchanged():
    text = "हवा तेज़ है"

    assert repair_mojibake(text) == text


def test_translate_to_english_collapses_whitespace():
    result = translate_to_english("  तेज़   हवा  ")

    assert result == "strong winds"


def test_malayalam_query_uses_groq_for_semantic_english_translation(
    monkeypatch,
):
    source = "കടലിലെ താപനില എത്രയാണ്?"
    calls = []

    def fake_groq(api_key, prompt, system_prompt):
        calls.append((api_key, prompt, system_prompt))
        return "What is the sea temperature?"

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(translator_module, "_call_groq_api", fake_groq)

    result = translate_to_english(source)

    assert result == "What is the sea temperature?"
    assert calls[0][0] == "test-key"
    assert calls[0][1] == source
    assert "Do not answer the question" in calls[0][2]


def test_english_query_does_not_call_groq(monkeypatch):
    def unexpected_groq(*args, **kwargs):
        raise AssertionError("English input should not call Groq")

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        translator_module,
        "_call_groq_api",
        unexpected_groq,
    )

    assert (
        translate_to_english("What is the sea temperature?")
        == "What is the sea temperature?"
    )


def test_malayalam_pfz_query_preserves_abbreviation(monkeypatch):
    source = "PFZ എവിടെയാണ്?"

    def fake_groq(api_key, prompt, system_prompt):
        return "Where is the PFZ?"

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(translator_module, "_call_groq_api", fake_groq)

    assert translate_to_english(source) == "Where is the PFZ?"


def test_malayalam_query_groq_failure_keeps_original(monkeypatch):
    source = "കടലിലെ താപനില എത്രയാണ്?"

    def failing_groq(*args, **kwargs):
        raise RuntimeError("temporary API failure")

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        translator_module,
        "_call_groq_api",
        failing_groq,
    )

    assert translate_to_english(source) == source


# ---------------------------------------------------------
# Multilingual marine glossary translation tests
# ---------------------------------------------------------


def test_pfz_is_preserved_in_hindi_translation():
    result = translate_response(
        "PFZ is useful for fishermen.",
        "hi",
    )

    assert "PFZ" in result


def test_sst_is_preserved_in_hindi_translation():
    result = translate_response(
        "SST is important for fishing.",
        "hi",
    )

    assert "SST" in result


def test_imbl_is_preserved_in_hindi_translation():
    result = translate_response(
        "IMBL is a maritime boundary.",
        "hi",
    )

    assert "IMBL" in result


def test_pfz_is_preserved_in_malayalam_translation():
    result = translate_response(
        "PFZ is useful for fishermen.",
        "ml",
    )

    assert "PFZ" in result


def test_sst_is_preserved_in_malayalam_translation():
    result = translate_response(
        "SST is important for fishing.",
        "ml",
    )

    assert "SST" in result


def test_imbl_is_preserved_in_tamil_translation():
    result = translate_response(
        "IMBL is a maritime boundary.",
        "ta",
    )

    assert "IMBL" in result


def test_sst_is_localized_to_hindi():
    result = translate_response(
        "Sea Surface Temperature is important.",
        "hi",
    )

    assert "समुद्र की सतह का तापमान" in result


def test_sst_is_localized_to_malayalam():
    result = translate_response(
        "Sea Surface Temperature is important.",
        "ml",
    )

    assert "കടൽ ഉപരിതല താപനില" in result


def test_sst_is_localized_to_tamil():
    result = translate_response(
        "Sea Surface Temperature is important.",
        "ta",
    )

    assert "கடல் மேற்பரப்பு வெப்பநிலை" in result


def test_pfz_is_localized_to_hindi():
    result = translate_response(
        "Potential Fishing Zone is useful.",
        "hi",
    )

    assert "मछली पकड़ने का संभावित क्षेत्र" in result


def test_pfz_is_localized_to_malayalam():
    result = translate_response(
        "Potential Fishing Zone is useful.",
        "ml",
    )

    assert "മത്സ്യബന്ധന സാധ്യതാ മേഖല" in result


def test_pfz_is_localized_to_tamil():
    result = translate_response(
        "Potential Fishing Zone is useful.",
        "ta",
    )

    assert "சாத்தியமான மீன்பிடி பகுதி" in result


def test_imbl_is_localized_to_hindi():
    result = translate_response(
        "International Maritime Boundary Line is important.",
        "hi",
    )

    assert "अंतरराष्ट्रीय समुद्री सीमा रेखा" in result


def test_imbl_is_localized_to_malayalam():
    result = translate_response(
        "International Maritime Boundary Line is important.",
        "ml",
    )

    assert "അന്താരാഷ്ട്ര സമുദ്ര അതിർത്തിരേഖ" in result


def test_imbl_is_localized_to_tamil():
    result = translate_response(
        "International Maritime Boundary Line is important.",
        "ta",
    )

    assert "சர்வதேச கடல் எல்லைக் கோடு" in result


def test_cyclone_is_localized_to_hindi():
    result = translate_response(
        "Cyclone warning is active.",
        "hi",
    )

    assert "चक्रवात" in result


def test_cyclone_is_localized_to_malayalam():
    result = translate_response(
        "Cyclone warning is active.",
        "ml",
    )

    assert "ചുഴലിക്കാറ്റ്" in result


def test_wave_height_is_localized_to_hindi():
    result = translate_response(
        "Wave Height is dangerous.",
        "hi",
    )

    assert "लहरों की ऊंचाई" in result


def test_wave_height_is_localized_to_malayalam():
    result = translate_response(
        "Wave Height is dangerous.",
        "ml",
    )

    assert "തിരമാലയുടെ ഉയരം" in result


def test_wind_speed_is_localized_to_hindi():
    result = translate_response(
        "Wind Speed is high.",
        "hi",
    )

    assert "हवा की गति" in result


def test_wind_speed_is_localized_to_malayalam():
    result = translate_response(
        "Wind Speed is high.",
        "ml",
    )

    assert "കാറ്റിന്റെ വേഗത" in result


def test_translate_text_uses_multilingual_glossary():
    result = translate_text(
        "Sea Surface Temperature is important.",
        "en",
        "ml",
    )

    assert result["source_language"] == "en"
    assert result["target_language"] == "ml"
    assert "കടൽ ഉപരിതല താപനില" in result["text"]
    assert "കടൽ ഉപരിതല താപനില" in result["translated_text"]


def test_abbreviations_are_not_expanded_repeatedly():
    result = translate_response(
        "PFZ and SST data are useful.",
        "hi",
    )

    assert result.count("PFZ") == 1
    assert result.count("SST") == 1


def test_malayalam_uses_groq_for_mixed_english_response(monkeypatch):
    source = (
        "The current Sea Surface Temperature (SST) is approximately "
        "**28.4°C**.\n\nThis reading is based on data from today."
    )
    translated = (
        "നിലവിലെ കടൽ ഉപരിതല താപനില (SST) ഏകദേശം **28.4°C** ആണ്."
        "\n\nഇന്നത്തെ ഡാറ്റയെ അടിസ്ഥാനമാക്കിയുള്ളതാണ് ഈ വായന."
    )
    calls = []

    def fake_groq(api_key, prompt, system_prompt):
        calls.append((api_key, prompt, system_prompt))
        return translated

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(translator_module, "_call_groq_api", fake_groq)

    result = translate_response(source, "ml")

    assert result == translated
    assert calls[0][0] == "test-key"
    assert calls[0][1] == source
    assert "Translate English into Malayalam" in calls[0][2]


def test_malayalam_missing_groq_key_keeps_deterministic_result(monkeypatch):
    source = "The current Sea Surface Temperature (SST) is 28.4°C."
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    result = translate_response(source, "ml")

    assert "കടൽ ഉപരിതല താപനില" in result
    assert "28.4°C" in result
    assert "is" in result


def test_malayalam_groq_failure_keeps_deterministic_result(monkeypatch):
    source = "The current Sea Surface Temperature (SST) is 28.4°C."

    def failing_groq(*args, **kwargs):
        raise RuntimeError("temporary API failure")

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        translator_module,
        "_call_groq_api",
        failing_groq,
    )

    result = translate_response(source, "ml")

    assert "കടൽ ഉപരിതല താപനില" in result
    assert "28.4°C" in result
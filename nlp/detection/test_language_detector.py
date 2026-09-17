from nlp.detection.language_detector import detect_language


def test_english_detection():
    result = detect_language("hello how are you")

    assert result["language_code"] == "en"


def test_malayalam_detection():
    result = detect_language("മഴ പെയ്യുന്നു")

    assert result["language_code"] == "ml"


def test_empty_text():
    result = detect_language("")

    assert result["language_code"] is None
    assert result["low_confidence"] is True


def test_invalid_input():
    try:
        detect_language(123)
        assert False, "Expected TypeError"
    except TypeError:
        assert True
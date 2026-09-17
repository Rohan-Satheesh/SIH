from nlp.translation.marine_glossary import (
    expand_terms,
    explain_term,
    get_localized_explanation,
    get_localized_term,
    localize_glossary_terms,
    lookup_term,
    normalize_term,
    protect_glossary_terms,
    restore_glossary_terms,
)


def test_lookup_pfz():
    result = lookup_term("PFZ")

    assert result is not None
    assert result["term"] == "Potential Fishing Zone"


def test_lookup_is_case_insensitive():
    result = lookup_term("sst")

    assert result is not None
    assert result["term"] == "Sea Surface Temperature"


def test_lookup_normalizes_spaces():
    result = lookup_term("  sea   surface   temperature  ")

    assert result is not None
    assert result["term"] == "Sea Surface Temperature"


def test_normalize_term():
    result = normalize_term("  wave   height ")

    assert result == "WAVE HEIGHT"


def test_unknown_term():
    result = lookup_term("UNKNOWN_TERM")

    assert result is None


def test_explain_term():
    result = explain_term("IMBL")

    assert "International Maritime Boundary Line" in result


def test_expand_terms():
    result = expand_terms("PFZ and SST data")

    assert "Potential Fishing Zone" in result
    assert "Sea Surface Temperature" in result


def test_expand_terms_does_not_duplicate():
    original = "PFZ (Potential Fishing Zone) and SST data"

    result = expand_terms(original)

    assert result.count("Potential Fishing Zone") == 1
    assert result.count("Sea Surface Temperature") == 1


def test_get_localized_term_hindi():
    result = get_localized_term("PFZ", "hi")

    assert result == "मछली पकड़ने का संभावित क्षेत्र"


def test_get_localized_term_malayalam():
    result = get_localized_term("SST", "ml")

    assert result == "കടൽ ഉപരിതല താപനില"


def test_get_localized_term_tamil():
    result = get_localized_term("IMBL", "ta")

    assert result == "சர்வதேச கடல் எல்லைக் கோடு"


def test_get_localized_term_english():
    result = get_localized_term("PFZ", "en")

    assert result == "Potential Fishing Zone"


def test_localized_explanation():
    result = get_localized_explanation("SST", "hi")

    assert "समुद्र की सतह का तापमान" in result
    assert "temperature" in result.lower()


def test_localize_glossary_terms_hindi():
    text = "Sea Surface Temperature is important."

    result = localize_glossary_terms(
        text,
        "hi",
    )

    assert "समुद्र की सतह का तापमान" in result


def test_localize_glossary_terms_malayalam():
    text = "Potential Fishing Zone is useful."

    result = localize_glossary_terms(
        text,
        "ml",
    )

    assert "മത്സ്യബന്ധന സാധ്യതാ മേഖല" in result


def test_protect_and_restore_terms():
    original = "PFZ and SST data are useful."

    protected_text, replacements = protect_glossary_terms(
        original,
    )

    assert "PFZ" not in protected_text
    assert "SST" not in protected_text
    assert "__ORCA_TERM_" in protected_text

    restored_text = restore_glossary_terms(
        protected_text,
        replacements,
    )

    assert restored_text == original


def test_unknown_language_raises_error():
    try:
        get_localized_term("PFZ", "xx")
        assert False, "Expected ValueError"
    except ValueError:
        assert True


def test_invalid_lookup_input():
    try:
        lookup_term(123)
        assert False, "Expected TypeError"
    except TypeError:
        assert True


def test_invalid_expand_input():
    try:
        expand_terms(123)
        assert False, "Expected TypeError"
    except TypeError:
        assert True
"""
Marine glossary utilities for ORCA NLP.

Provides:

- Marine glossary definitions
- Term lookup
- Term normalization
- Abbreviation expansion
- Localized term lookup
- Localized explanations
- Glossary term localization
- Glossary term protection/restoration
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Supported languages
# ---------------------------------------------------------------------------

SUPPORTED_GLOSSARY_LANGUAGES = {
    "en",
    "hi",
    "ta",
    "te",
    "ml",
    "kn",
    "bn",
    "mr",
    "gu",
    "or",
}


# ---------------------------------------------------------------------------
# Marine glossary
# ---------------------------------------------------------------------------

MARINE_GLOSSARY: dict[str, dict[str, Any]] = {
    "SST": {
        "term": "Sea Surface Temperature",
        "full_form": "Sea Surface Temperature",
        "definition": (
            "The temperature of seawater near the ocean surface. "
            "It is useful for studying marine weather, ocean conditions, "
            "and identifying possible fishing zones."
        ),
        "explanation": (
            "Sea Surface Temperature is the temperature of seawater "
            "near the ocean surface. It helps identify ocean conditions "
            "that may be suitable for fish."
        ),
        "category": "oceanographic",
        "translations": {
            "en": "Sea Surface Temperature",
            "hi": "समुद्र की सतह का तापमान",
            "ta": "கடல் மேற்பரப்பு வெப்பநிலை",
            "te": "సముద్ర ఉపరితల ఉష్ణోగ్రత",
            "ml": "കടൽ ഉപരിതല താപനില",
            "kn": "ಸಮುದ್ರ ಮೇಲ್ಮೈ ತಾಪಮಾನ",
            "bn": "সমুদ্রপৃষ্ঠের তাপমাত্রা",
            "mr": "समुद्राच्या पृष्ठभागाचे तापमान",
            "gu": "સમુદ્રની સપાટીનું તાપમાન",
            "or": "ସମୁଦ୍ର ପୃଷ୍ଠ ତାପମାତ୍ରା",
        },
    },
    "PFZ": {
        "term": "Potential Fishing Zone",
        "full_form": "Potential Fishing Zone",
        "definition": (
            "An area of the sea where environmental conditions are "
            "favorable for the presence of fish."
        ),
        "explanation": (
            "A Potential Fishing Zone is an area of the sea where "
            "environmental conditions are favorable for fish availability. "
            "These zones may be identified using sea surface temperature, "
            "ocean colour, chlorophyll, and other ocean data."
        ),
        "category": "fishing",
        "translations": {
            "en": "Potential Fishing Zone",
            "hi": "मछली पकड़ने का संभावित क्षेत्र",
            "ta": "சாத்தியமான மீன்பிடி பகுதி",
            "te": "సంభావ్య చేపల వేట ప్రాంతం",
            "ml": "മത്സ്യബന്ധന സാധ്യതാ മേഖല",
            "kn": "ಸಂಭಾವ್ಯ ಮೀನುಗಾರಿಕೆ ವಲಯ",
            "bn": "সম্ভাব্য মাছ ধরার অঞ্চল",
            "mr": "संभाव्य मासेमारी क्षेत्र",
            "gu": "સંભવિત માછીમારી વિસ્તાર",
            "or": "ସମ୍ଭାବ୍ୟ ମାଛ ଧରିବା ଅଞ୍ଚଳ",
        },
    },
    "IMBL": {
        "term": "International Maritime Boundary Line",
        "full_form": "International Maritime Boundary Line",
        "definition": (
            "A maritime boundary separating the maritime zones "
            "of two countries."
        ),
        "explanation": (
            "The International Maritime Boundary Line is a boundary "
            "separating the maritime zones of two countries. Fishermen "
            "must avoid crossing it without proper authorization."
        ),
        "category": "maritime_boundary",
        "translations": {
            "en": "International Maritime Boundary Line",
            "hi": "अंतरराष्ट्रीय समुद्री सीमा रेखा",
            "ta": "சர்வதேச கடல் எல்லைக் கோடு",
            "te": "అంతర్జాతీయ సముద్ర సరిహద్దు రేఖ",
            "ml": "അന്താരാഷ്ട്ര സമുദ്ര അതിർത്തിരേഖ",
            "kn": "ಅಂತರರಾಷ್ಟ್ರೀಯ ಸಮುದ್ರ ಗಡಿ ರೇಖೆ",
            "bn": "আন্তর্জাতিক সামুদ্রিক সীমারেখা",
            "mr": "आंतरराष्ट्रीय सागरी सीमा रेषा",
            "gu": "આંતરરાષ્ટ્રીય દરિયાઈ સીમા રેખા",
            "or": "ଆନ୍ତର୍ଜାତୀୟ ସାମୁଦ୍ରିକ ସୀମା ରେଖା",
        },
    },
    "SST ANOMALY": {
        "term": "Sea Surface Temperature Anomaly",
        "full_form": "Sea Surface Temperature Anomaly",
        "definition": (
            "The difference between the observed sea surface temperature "
            "and its long-term average."
        ),
        "explanation": (
            "Sea Surface Temperature Anomaly describes how much the current "
            "sea surface temperature differs from its usual average."
        ),
        "category": "oceanographic",
        "translations": {
            "en": "Sea Surface Temperature Anomaly",
            "hi": "समुद्र की सतह के तापमान में असामान्यता",
            "ta": "கடல் மேற்பரப்பு வெப்பநிலை விலகல்",
            "te": "సముద్ర ఉపరితల ఉష్ణోగ్రత వ్యత్యాసం",
            "ml": "കടൽ ഉപരിതല താപനില വ്യതിയാനം",
            "kn": "ಸಮುದ್ರ ಮೇಲ್ಮೈ ತಾಪಮಾನ ವ್ಯತ್ಯಾಸ",
            "bn": "সমুদ্রপৃষ্ঠের তাপমাত্রার অস্বাভাবিকতা",
            "mr": "समुद्राच्या पृष्ठभागाच्या तापमानातील विसंगती",
            "gu": "સમુદ્રની સપાટીના તાપમાનમાં અસામાન્યતા",
            "or": "ସମୁଦ୍ର ପୃଷ୍ଠ ତାପମାତ୍ରା ବିସଙ୍ଗତି",
        },
    },
    "CHLOROPHYLL": {
        "term": "Chlorophyll-a",
        "full_form": "Chlorophyll-a",
        "definition": (
            "A pigment found in phytoplankton that is commonly used "
            "as an indicator of ocean productivity."
        ),
        "explanation": (
            "Chlorophyll-a is a pigment found in phytoplankton. "
            "Its concentration can help indicate biological productivity "
            "and possible fish-rich areas."
        ),
        "category": "oceanographic",
        "translations": {
            "en": "Chlorophyll-a",
            "hi": "क्लोरोफिल-ए",
            "ta": "குளோரோபில்-ஏ",
            "te": "క్లోరోఫిల్-ఎ",
            "ml": "ക്ലോറോഫിൽ-എ",
            "kn": "ಕ್ಲೋರೊಫಿಲ್-ಎ",
            "bn": "ক্লোরোফিল-এ",
            "mr": "क्लोरोफिल-ए",
            "gu": "ક્લોરોફિલ-એ",
            "or": "କ୍ଲୋରୋଫିଲ୍-ଏ",
        },
    },
}


# ---------------------------------------------------------------------------
# Abbreviation expansions
# ---------------------------------------------------------------------------

ABBREVIATION_EXPANSIONS: dict[str, str] = {
    "SST": "Sea Surface Temperature",
    "PFZ": "Potential Fishing Zone",
    "IMBL": "International Maritime Boundary Line",
}


# Backward-compatible alias
GLOSSARY = MARINE_GLOSSARY


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_text(value: str) -> str:
    """Normalize text for internal comparisons."""
    return " ".join(value.strip().upper().split())


def _term_pattern(term: str) -> re.Pattern[str]:
    """Create a case-insensitive whole-term regex pattern."""
    return re.compile(
        rf"(?<!\w){re.escape(term)}(?!\w)",
        flags=re.IGNORECASE,
    )


def _find_glossary_entry(
    term: str,
) -> tuple[str, dict[str, Any]] | None:
    """Find an entry using either abbreviation or full English term."""
    if not isinstance(term, str):
        raise TypeError("term must be a string")

    normalized_term = _normalize_text(term)

    for key, details in MARINE_GLOSSARY.items():
        possible_names = {
            _normalize_text(key),
            _normalize_text(str(details.get("term", ""))),
            _normalize_text(str(details.get("full_form", ""))),
        }

        if normalized_term in possible_names:
            return key, details

    return None


# ---------------------------------------------------------------------------
# Public lookup functions
# ---------------------------------------------------------------------------

def normalize_term(term: str) -> str:
    """
    Normalize a term by:

    - Removing leading/trailing spaces
    - Replacing repeated spaces with one space
    - Converting to uppercase

    Example:
        "  wave   height " -> "WAVE HEIGHT"
    """
    if not isinstance(term, str):
        raise TypeError("term must be a string")

    return _normalize_text(term)


def lookup_term(term: str) -> dict[str, Any] | None:
    """
    Look up a glossary term.

    Supports:

    - Abbreviations such as PFZ
    - Full terms such as Potential Fishing Zone

    Returns None when the term is not found.
    """
    result = _find_glossary_entry(term)

    if result is None:
        return None

    _, details = result
    return details


def get_localized_term(
    term: str,
    language_code: str = "en",
) -> str | None:
    """
    Return the localized name of a glossary term.
    """
    result = _find_glossary_entry(term)

    if result is None:
        return None

    if not isinstance(language_code, str):
        raise TypeError("language_code must be a string")

    language_code = language_code.strip().lower()

    if language_code not in SUPPORTED_GLOSSARY_LANGUAGES:
        raise ValueError(
            f"Unsupported glossary language: {language_code}"
        )

    _, details = result
    translations = details.get("translations", {})

    return translations.get(
        language_code,
        translations.get("en", details.get("term", term)),
    )


def explain_term(term: str) -> str:
    """
    Return the English explanation of a glossary term.

    Returns an empty string for an unknown term.
    """
    result = _find_glossary_entry(term)

    if result is None:
        return ""

    _, details = result

    return str(
        details.get(
            "explanation",
            details.get("definition", ""),
        )
    )


def get_localized_explanation(
    term: str,
    language_code: str = "en",
) -> str:
    """
    Return a glossary explanation containing the localized term.

    The explanation text is currently in English. The localized term
    is included so that users can understand the marine terminology.
    """
    result = lookup_term(term)

    if result is None:
        return f"No glossary explanation found for '{term}'."

    localized_term = get_localized_term(
        term,
        language_code,
    )

    explanation = str(
        result.get(
            "definition",
            result.get("explanation", ""),
        )
    )

    return f"{localized_term}: {explanation}"


# ---------------------------------------------------------------------------
# Abbreviation expansion
# ---------------------------------------------------------------------------

def expand_terms(text: str) -> str:
    """
    Expand marine abbreviations without duplicating existing expansions.

    Example:

        PFZ and SST data

    becomes:

        PFZ (Potential Fishing Zone) and
        SST (Sea Surface Temperature) data

    Existing text such as:

        PFZ (Potential Fishing Zone)

    is not duplicated.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    expanded_text = text

    abbreviations = sorted(
        ABBREVIATION_EXPANSIONS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for abbreviation, full_form in abbreviations:
        existing_expansion_pattern = re.compile(
            rf"\b{re.escape(abbreviation)}\s*"
            rf"\(\s*{re.escape(full_form)}\s*\)",
            flags=re.IGNORECASE,
        )

        if existing_expansion_pattern.search(expanded_text):
            continue

        abbreviation_pattern = re.compile(
            rf"\b{re.escape(abbreviation)}\b",
            flags=re.IGNORECASE,
        )

        expanded_text = abbreviation_pattern.sub(
            f"{abbreviation} ({full_form})",
            expanded_text,
        )

    return expanded_text


# ---------------------------------------------------------------------------
# Glossary localization
# ---------------------------------------------------------------------------

def localize_glossary_terms(
    text: str,
    language_code: str = "en",
) -> str:
    """
    Replace recognized English glossary terms with localized terms.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    language_code = language_code.strip().lower()

    if language_code not in SUPPORTED_GLOSSARY_LANGUAGES:
        raise ValueError(
            f"Unsupported glossary language: {language_code}"
        )

    localized_text = text
    replacements: list[tuple[str, str]] = []

    for key, details in MARINE_GLOSSARY.items():
        english_names = {
            str(details.get("term", "")),
            str(details.get("full_form", "")),
        }

        for english_name in english_names:
            if not english_name.strip():
                continue

            localized_name = get_localized_term(
                english_name,
                language_code,
            )

            if localized_name:
                replacements.append(
                    (english_name, localized_name)
                )

    for english_phrase, translations in MARINE_PHRASE_TRANSLATIONS.items():
        localized_phrase = translations.get(
            language_code,
            translations.get("en", english_phrase),
        )
        if localized_phrase:
            replacements.append(
                (english_phrase, localized_phrase)
            )

    # Replace longer terms first.
    replacements.sort(
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for english_name, localized_name in replacements:
        pattern = _term_pattern(english_name)

        localized_text = pattern.sub(
            lambda _: localized_name,
            localized_text,
        )

    return localized_text


# ---------------------------------------------------------------------------
# Protection and restoration
# ---------------------------------------------------------------------------

def protect_glossary_terms(
    text: str,
) -> tuple[str, dict[str, str]]:
    """
    Replace marine abbreviations with ORCA placeholders.

    Example:

        PFZ and SST data

    becomes something similar to:

        __ORCA_TERM_0__ and __ORCA_TERM_1__ data
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    protected_text = text
    replacements: dict[str, str] = {}

    abbreviations = sorted(
        ABBREVIATION_EXPANSIONS.keys(),
        key=len,
        reverse=True,
    )

    placeholder_index = 0

    for abbreviation in abbreviations:
        pattern = re.compile(
            rf"\b{re.escape(abbreviation)}\b",
            flags=re.IGNORECASE,
        )

        while True:
            match = pattern.search(protected_text)

            if match is None:
                break

            placeholder = (
                f"__ORCA_TERM_{placeholder_index}__"
            )

            original_term = match.group(0)

            protected_text = (
                protected_text[:match.start()]
                + placeholder
                + protected_text[match.end():]
            )

            replacements[placeholder] = original_term
            placeholder_index += 1

    return protected_text, replacements


def restore_glossary_terms(
    text: str,
    replacements: dict[str, str],
) -> str:
    """
    Restore glossary terms from ORCA placeholders.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not isinstance(replacements, dict):
        raise TypeError("replacements must be a dictionary")

    restored_text = text

    for placeholder, original_term in replacements.items():
        restored_text = restored_text.replace(
            placeholder,
            original_term,
        )

    return restored_text


# ---------------------------------------------------------------------------
# Backward-compatible aliases
# ---------------------------------------------------------------------------

def localize_term(
    term: str,
    language_code: str = "en",
) -> str | None:
    """Alias for get_localized_term()."""
    return get_localized_term(term, language_code)


def localized_explanation(
    term: str,
    language_code: str = "en",
) -> str:
    """Alias for get_localized_explanation()."""
    return get_localized_explanation(term, language_code)


# ---------------------------------------------------------------------------
# Public exports
# ---------------------------------------------------------------------------

__all__ = [
    "MARINE_PHRASE_TRANSLATIONS",
    "SUPPORTED_GLOSSARY_LANGUAGES",
    "MARINE_GLOSSARY",
    "ABBREVIATION_EXPANSIONS",
    "GLOSSARY",
    "normalize_term",
    "lookup_term",
    "get_localized_term",
    "explain_term",
    "get_localized_explanation",
    "expand_terms",
    "localize_glossary_terms",
    "protect_glossary_terms",
    "restore_glossary_terms",
    "localize_term",
    "localized_explanation",
]

MARINE_PHRASE_TRANSLATIONS: dict[str, dict[str, str]] = {
    "wave height": {
        "en": "Wave Height",
        "hi": "लहरों की ऊंचाई",
        "ta": "அலை உயரம்",
        "te": "అలల ఎత్తు",
        "ml": "തിരമാലയുടെ ഉയരം",
        "kn": "ಅಲೆಗಳ ಎತ್ತರ",
        "bn": "ঢেউয়ের উচ্চতা",
        "mr": "लाटांची उंची",
        "gu": "મોજાંની ઊંચાઈ",
        "or": "ତରଙ୍ଗର ଉଚ୍ଚତା",
    },
    "wind speed": {
        "en": "Wind Speed",
        "hi": "हवा की गति",
        "ta": "காற்றின் வேகம்",
        "te": "గాలి వేగం",
        "ml": "കാറ്റിന്റെ വേഗത",
        "kn": "ಗಾಳಿಯ ವೇಗ",
        "bn": "বাতাসের গতি",
        "mr": "वाऱ्याचा वेग",
        "gu": "પવનની ગતિ",
        "or": "ପବନର ବେଗ",
    },
    "cyclone": {
        "en": "Cyclone",
        "hi": "चक्रवात",
        "ta": "சூறாவளி",
        "te": "తుఫాను",
        "ml": "ചുഴലിക്കാറ്റ്",
        "kn": "ಚಂಡಮಾರುತ",
        "bn": "ঘূর্ণিঝড়",
        "mr": "चक्रीवादळ",
        "gu": "વાવાઝોડું",
        "or": "ବାତ୍ୟା",
    },
}
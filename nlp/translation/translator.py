"""
Translation utilities for ORCA_NLP.

Supports:
- Language validation
- Mojibake repair
- Lightweight phrase translation
- Full ORCA response translation
- Multilingual marine glossary
- Marine abbreviation protection
"""

from __future__ import annotations

import logging
import os
import re

from nlp.llm.groq_client import _call_groq_api

from .marine_glossary import (
    localize_glossary_terms,
    protect_glossary_terms,
    restore_glossary_terms,
)


logger = logging.getLogger(__name__)


SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "ml": "Malayalam",
    "te": "Telugu",
    "kn": "Kannada",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "or": "Odia",
}

MARINE_PHRASE_TRANSLATIONS = {
    "Sea Surface Temperature": {
        "hi": "समुद्र की सतह का तापमान",
        "ta": "கடல் மேற்பரப்பு வெப்பநிலை",
        "ml": "കടൽ ഉപരിതല താപനില",
        "te": "సముద్ర ఉపరితల ఉష్ణోగ్రత",
        "kn": "ಸಮುದ್ರ ಮೇಲ್ಮೈ ತಾಪಮಾನ",
        "bn": "সমুদ্রপৃষ্ঠের তাপমাত্রা",
        "mr": "समुद्राच्या पृष्ठभागाचे तापमान",
        "gu": "સમુદ્રની સપાટીનું તાપમાન",
        "or": "ସମୁଦ୍ର ପୃଷ୍ଠ ତାପମାତ୍ରା",
    },

    "Wave Height": {
        "hi": "लहरों की ऊंचाई",
        "ta": "அலைகளின் உயரம்",
        "ml": "തിരമാലയുടെ ഉയരം",
        "te": "అలల ఎత్తు",
        "kn": "ಅಲೆಗಳ ಎತ್ತರ",
        "bn": "তরঙ্গের উচ্চতা",
        "mr": "लाटांची उंची",
        "gu": "મોજાંની ઊંચાઈ",
        "or": "ତରଙ୍ଗର ଉଚ୍ଚତା",
    },

    "Wind Speed": {
        "hi": "हवा की गति",
        "ta": "காற்றின் வேகம்",
        "ml": "കാറ്റിന്റെ വേഗത",
        "te": "గాలి వేగం",
        "kn": "ಗಾಳಿಯ ವೇಗ",
        "bn": "বাতাসের গতি",
        "mr": "वाऱ्याचा वेग",
        "gu": "પવનની ગતિ",
        "or": "ପବନର ବେଗ",
    },
}

def _translate_exact_marine_phrases(
    text: str,
    target_language: str,
) -> str:
    translated_text = text

    for english_phrase, translations in MARINE_PHRASE_TRANSLATIONS.items():
        translated_phrase = translations.get(target_language)

        if translated_phrase is None:
            continue

        pattern = rf"(?<!\w){re.escape(english_phrase)}(?!\w)"

        translated_text = re.sub(
            pattern,
            translated_phrase,
            translated_text,
            flags=re.IGNORECASE,
        )

    return translated_text

TRANSLATION_MAP = {
    # Hindi
    "तेज़ हवा": "strong winds",
    "तेज हवा": "strong winds",
    "तेज़ हवाएं": "strong winds",
    "तेज हवाएं": "strong winds",
    "तेज़ हवाएँ": "strong winds",
    "तेज हवाएँ": "strong winds",
    "भारी बारिश": "heavy rain",
    "हल्की बारिश": "light rain",
    "मध्यम बारिश": "moderate rain",
    "अच्छा मौसम": "good weather",
    "खराब मौसम": "bad weather",
    "तापमान": "temperature",
    "नमी": "humidity",
    "किसान": "farmer",
    "फसल": "crop",
    "मिट्टी": "soil",
    "पानी": "water",

    # Tamil
    "பலத்த காற்று": "strong winds",
    "கனமழை": "heavy rain",
    "லேசான மழை": "light rain",
    "வெப்பநிலை": "temperature",
    "ஈரப்பதம்": "humidity",
    "விவசாயி": "farmer",
    "பயிர்": "crop",
    "மண்": "soil",
    "தண்ணீர்": "water",

    # Telugu
    "బలమైన గాలులు": "strong winds",
    "భారీ వర్షం": "heavy rain",
    "తేలికపాటి వర్షం": "light rain",
    "ఉష్ణోగ్రత": "temperature",
    "తేమ": "humidity",
    "రైతు": "farmer",
    "పంట": "crop",
    "నేల": "soil",
    "నీరు": "water",

    # Kannada
    "ಬಲವಾದ ಗಾಳಿ": "strong winds",
    "ಭಾರಿ ಮಳೆ": "heavy rain",
    "ಲಘು ಮಳೆ": "light rain",
    "ತಾಪಮಾನ": "temperature",
    "ತೇವಾಂಶ": "humidity",
    "ರೈತ": "farmer",
    "ಬೆಳೆ": "crop",
    "ಮಣ್ಣು": "soil",
    "ನೀರು": "water",

    # Bengali
    "প্রবল বাতাস": "strong winds",
    "ভারী বৃষ্টি": "heavy rain",
    "হালকা বৃষ্টি": "light rain",
    "তাপমাত্রা": "temperature",
    "আর্দ্রতা": "humidity",
    "কৃষক": "farmer",
    "ফসল": "crop",
    "মাটি": "soil",
    "জল": "water",

    # Marathi
    "जोरदार वारे": "strong winds",
    "मुसळधार पाऊस": "heavy rain",
    "हलका पाऊस": "light rain",
    "तापमान": "temperature",
    "आर्द्रता": "humidity",
    "शेतकरी": "farmer",
    "पीक": "crop",
    "माती": "soil",
    "पाणी": "water",

    # Gujarati
    "તીવ્ર પવન": "strong winds",
    "ભારે વરસાદ": "heavy rain",
    "હળવો વરસાદ": "light rain",
    "તાપમાન": "temperature",
    "ભેજ": "humidity",
    "ખેડૂત": "farmer",
    "પાક": "crop",
    "માટી": "soil",
    "પાણી": "water",

    # Odia
    "ପ୍ରବଳ ପବନ": "strong winds",
    "ପ୍ରବଳ ବର୍ଷା": "heavy rain",
    "ହାଲୁକା ବର୍ଷା": "light rain",
    "ତାପମାତ୍ରା": "temperature",
    "ଆର୍ଦ୍ରତା": "humidity",
    "ଚାଷୀ": "farmer",
    "ଫସଲ": "crop",
    "ମାଟି": "soil",
    "ପାଣି": "water",
}


HINDI_RESPONSE_MAP = {
    "strong winds": "तेज़ हवा",
    "heavy rain": "भारी बारिश",
    "light rain": "हल्की बारिश",
    "moderate rain": "मध्यम बारिश",
    "good weather": "अच्छा मौसम",
    "bad weather": "खराब मौसम",
    "temperature": "तापमान",
    "humidity": "नमी",
    "farmer": "किसान",
    "crop": "फसल",
    "soil": "मिट्टी",
    "water": "पानी",
}


TAMIL_RESPONSE_MAP = {
    "strong winds": "பலத்த காற்று",
    "heavy rain": "கனமழை",
    "light rain": "லேசான மழை",
    "moderate rain": "மிதமான மழை",
    "temperature": "வெப்பநிலை",
    "humidity": "ஈரப்பதம்",
    "farmer": "விவசாயி",
    "crop": "பயிர்",
    "soil": "மண்",
    "water": "தண்ணீர்",
}


HINDI_FULL_RESPONSE_MAP = {
    "strong_wind_warning": (
        "⚠️ तेज़ हवा की चेतावनी\n\n"
        "तेज़ हवाएं नाव की स्थिरता और समुद्र में दिशा बनाए रखने को प्रभावित कर सकती हैं।\n"
        "समुद्र में जाने से पहले हवा की गति का पूर्वानुमान जांचें।\n"
        "छोटी नावों को असुरक्षित मौसम की स्थिति से बचना चाहिए।"
    ),

    "high_wave_warning": (
        "⚠️ ऊंची लहरों की चेतावनी\n\n"
        "ऊंची लहरें समुद्री यात्रा को खतरनाक बना सकती हैं।\n"
        "ऊंची लहरों के दौरान छोटी नावों को समुद्र में जाने से बचना चाहिए।\n"
        "लहरों की ऊंचाई का पूर्वानुमान जांचें और स्थिति खराब होने पर "
        "सुरक्षित बंदरगाह की ओर जाएं।"
    ),

    "cyclone_warning": (
        "⚠️ चक्रवात की चेतावनी\n\n"
        "चक्रवात की स्थिति मछुआरों के लिए बेहद खतरनाक हो सकती है।\n"
        "चक्रवात की चेतावनी के दौरान समुद्र में न जाएं।\n"
        "आधिकारिक मौसम सलाह का पालन करें और सुरक्षित बंदरगाह की ओर जाएं।"
    ),

    "unsafe_weather_warning": (
        "⚠️ असुरक्षित मौसम की चेतावनी\n\n"
        "मौसम की स्थिति समुद्री यात्रा के लिए खतरनाक हो सकती है।\n"
        "हवा, लहरों, बारिश और चक्रवात की चेतावनियों का पूर्वानुमान जांचें।\n"
        "स्थिति खराब होने पर किनारे लौटें या सुरक्षित बंदरगाह की ओर जाएं।"
    ),

    "return_to_shore": (
        "⚠️ सुरक्षा चेतावनी\n\n"
        "समुद्र की स्थिति खतरनाक हो सकती है।\n"
        "तुरंत किनारे लौटें या निकटतम सुरक्षित बंदरगाह की ओर जाएं।\n"
        "आधिकारिक समुद्री सुरक्षा चेतावनियों का पालन करें।"
    ),

    "pfz": (
        "PFZ का पूरा नाम Potential Fishing Zone है।\n\n"
        "PFZ ऐसे क्षेत्र होते हैं जहां मछलियां अधिक मात्रा में मिल सकती हैं।\n"
        "इन क्षेत्रों का अनुमान समुद्र की सतह के तापमान, "
        "क्लोरोफिल की मात्रा, समुद्र के रंग और समुद्री सीमाओं जैसी "
        "जानकारियों से लगाया जा सकता है।\n\n"
        "PFZ केवल एक सुझाव है और यह मछलियों की उपलब्धता की गारंटी नहीं देता।\n"
        "मछुआरों को PFZ जानकारी के साथ स्थानीय ज्ञान, मौसम की स्थिति, "
        "नाव की क्षमता और सुरक्षा चेतावनियों को भी ध्यान में रखना चाहिए।"
    ),

    "sst": (
        "SST का पूरा नाम Sea Surface Temperature है।\n\n"
        "यह समुद्र की सतह के पानी का तापमान बताता है।"
    ),

    "imbl": (
        "IMBL का पूरा नाम International Maritime Boundary Line है।\n\n"
        "यह दो तटीय देशों या समुद्री क्षेत्रों के बीच की समुद्री सीमा होती है।"
    ),

    "weather_forecast": (
        "समुद्र में जाने से पहले नवीनतम आधिकारिक मौसम पूर्वानुमान जांचें।\n\n"
        "हवा की गति, लहरों की ऊंचाई, बारिश और चक्रवात की चेतावनियों पर ध्यान दें।"
    ),

    "safety_check": (
        "समुद्र में जाने से पहले मछुआरों को मौसम का पूर्वानुमान, "
        "हवा की गति, लहरों की ऊंचाई, बारिश और चक्रवात की चेतावनियां जांचनी चाहिए।\n\n"
        "छोटी नावों को खराब मौसम, ऊंची लहरों, तेज़ हवाओं और चक्रवात की "
        "स्थिति से बचना चाहिए।\n\n"
        "लाइफ जैकेट, संचार उपकरण, पीने का पानी, प्राथमिक उपचार की सामग्री "
        "और आपातकालीन उपकरण साथ रखें।"
    ),
}

MALAYALAM_FULL_RESPONSE_MAP = {
    "strong_wind_warning": (
        "⚠️ ശക്തമായ കാറ്റ് മുന്നറിയിപ്പ്\n\n"
        "ശക്തമായ കാറ്റ് ബോട്ടിന്റെ സ്ഥിരതയെ ബാധിക്കും.\n"
        "കടലിൽ പോകുന്നതിന് മുൻപ് കാറ്റിന്റെ വേഗത പരിശോധിക്കുക.\n"
        "ചെറിയ ബോട്ടുകൾ മോശം കാലാവസ്ഥയിൽ കടലിൽ പോകുന്നത് ഒഴിവാക്കുക."
    ),

    "high_wave_warning": (
        "⚠️ ഉയർന്ന തിരമാല മുന്നറിയിപ്പ്\n\n"
        "ഉയർന്ന തിരമാലകൾ കടൽയാത്ര അപകടകരമാക്കാം.\n"
        "ചെറിയ ബോട്ടുകൾ കടലിൽ പോകുന്നത് ഒഴിവാക്കുക.\n"
        "സാഹചര്യം മോശമായാൽ അടുത്തുള്ള സുരക്ഷിത തുറമുഖത്തേക്ക് മാറുക."
    ),

    "cyclone_warning": (
        "⚠️ ചുഴലിക്കാറ്റ് മുന്നറിയിപ്പ്\n\n"
        "ചുഴലിക്കാറ്റ് മുന്നറിയിപ്പുള്ളപ്പോൾ കടലിൽ പോകരുത്.\n"
        "ഔദ്യോഗിക നിർദ്ദേശങ്ങൾ പാലിച്ച് സുരക്ഷിത തുറമുഖത്ത് പ്രവേശിക്കുക."
    ),

    "unsafe_weather_warning": (
        "⚠️ മോശം കാലാവസ്ഥ മുന്നറിയിപ്പ്\n\n"
        "കടൽ കാലാവസ്ഥ മോശമാകുന്ന സാഹചര്യത്തിൽ തീരത്തേക്ക് മടങ്ങുക അല്ലെങ്കിൽ സുരക്ഷിത തുറമുഖത്തേക്ക് മാറുക."
    ),

    "return_to_shore": (
        "⚠️ സുരക്ഷാ മുന്നറിയിപ്പ്\n\n"
        "ഉടൻ തീരത്തേക്ക് മടങ്ങുക അല്ലെങ്കിൽ അടുത്തുള്ള സുരക്ഷിത തുറമുഖത്ത് പ്രവേശിക്കുക.\n"
        "ഔദ്യോഗിക സുരക്ഷാ നിർദ്ദേശങ്ങൾ പാലിക്കുക."
    ),

    "pfz": (
        "PFZ എന്നാൽ Potential Fishing Zone (മത്സ്യബന്ധന സാധ്യതാ മേഖല) ആണ്.\n\n"
        "കടൽ ഉപരിതല താപനില (SST), ക്ലോറോഫിൽ സാന്ദ്രത, സമുദ്ര പ്രവാഹങ്ങൾ എന്നിവ അടിസ്ഥാനമാക്കി മീനുകൾ കൂട്ടമായി കാണാൻ സാധ്യതയുള്ള മേഖലകളാണ് ഇവ.\n\n"
        "PFZ വിവരങ്ങൾ ഒരു ശാസ്ത്രീയ നിർദ്ദേശമാണ്, മത്സ്യം ലഭിക്കുമെന്ന പൂർണ്ണ ഉറപ്പല്ല. കടലിൽ പോകുന്നതിന് മുൻപ് കാലാവസ്ഥ, കാറ്റിന്റെയും തിരമാലയുടെയും മുന്നറിയിപ്പുകൾ, ബോട്ടിന്റെ ശേഷി എന്നിവ നിർബന്ധമായും ശ്രദ്ധിക്കുക."
    ),

    "sst": (
        "SST എന്നാൽ Sea Surface Temperature (കടൽ ഉപരിതല താപനില) ആണ്.\n\n"
        "ഇത് കടലിന്റെ ഉപരിതലത്തിലെ വെള്ളത്തിന്റെ താപനിലയെ സൂചിപ്പിക്കുന്നു. മീനുകൾ കൂടുന്ന മേഖലകൾ കണ്ടെത്താൻ ഇത് സഹായിക്കുന്നു."
    ),

    "imbl": (
        "IMBL എന്നാൽ International Maritime Boundary Line (അന്താരാഷ്ട്ര സമുദ്ര അതിർത്തിരേഖ) ആണ്.\n\n"
        "ഇത് രണ്ട് രാജ്യങ്ങൾ തമ്മിലുള്ള ഔദ്യോഗിക സമുദ്ര അതിർത്തിയാണ്. സുരക്ഷ ഉറപ്പാക്കാൻ മത്സ്യത്തൊഴിലാളികൾ IMBL മറികടക്കരുത്."
    ),

    "weather_forecast": (
        "കടലിൽ പോകുന്നതിന് മുൻപ് ഔദ്യോഗിക കാലാവസ്ഥാ പ്രവചനം പരിശോധിക്കുക.\n\n"
        "കാറ്റിന്റെ വേഗത, തിരമാലയുടെ ഉയരം, മഴ, ചുഴലിക്കാറ്റ് മുന്നറിയിപ്പുകൾ എന്നിവ ശ്രദ്ധിക്കുക."
    ),

    "safety_check": (
        "കടലിൽ പോകുന്നതിന് മുൻപ് കാലാവസ്ഥ, കാറ്റ്, തിരമാല എന്നിവ പരിശോധിക്കുക.\n\n"
        "എല്ലാ തൊഴിലാളികൾക്കും ലൈഫ് ജാക്കറ്റുകൾ, ആശയവിനിമയ ഉപകരണങ്ങൾ, അടിയന്തര സുരക്ഷാ സാമഗ്രികൾ എന്നിവ നിർബന്ധമായും കരുതുക."
    ),
}


# Exact marine phrase translations.
# These are applied before the generic glossary localization.
MARINE_PHRASE_MAP = {
    "ta": {
        "sea surface temperature": "கடல் மேற்பரப்பு வெப்பநிலை",
        "wave height": "அலை உயரம்",
        "wind speed": "காற்றின் வேகம்",
        "cyclone": "சுழற்காற்று",
        "international maritime boundary line": (
            "சர்வதேச கடல் எல்லைக் கோடு"
        ),
        "potential fishing zone": "சாத்தியமான மீன்பிடி பகுதி",
    },

    "ml": {
        "sea surface temperature": "കടൽ ഉപരിതല താപനില",
        "wave height": "തിരമാലയുടെ ഉയരം",
        "wind speed": "കാറ്റിന്റെ വേഗത",
        "cyclone": "ചുഴലിക്കാറ്റ്",
        "international maritime boundary line": (
            "അന്താരാഷ്ട്ര സമുദ്ര അതിർത്തിരേഖ"
        ),
        "potential fishing zone": (
            "മത്സ്യബന്ധന സാധ്യതാ മേഖല"
        ),
    },

    "hi": {
        "sea surface temperature": "समुद्र की सतह का तापमान",
        "wave height": "लहरों की ऊंचाई",
        "wind speed": "हवा की गति",
        "cyclone": "चक्रवात",
        "international maritime boundary line": (
            "अंतरराष्ट्रीय समुद्री सीमा रेखा"
        ),
        "potential fishing zone": (
            "मछली पकड़ने का संभावित क्षेत्र"
        ),
    },
}


def is_supported_language(language_code: str) -> bool:
    """
    Return True if the language code is supported.
    """

    if not isinstance(language_code, str):
        return False

    return language_code.strip().lower() in SUPPORTED_LANGUAGES


def repair_mojibake(text: str) -> str:
    """
    Repair incorrectly decoded UTF-8 text when possible.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not text:
        return text

    mojibake_markers = (
        "Ã",
        "Â",
        "â",
        "ð",
        "à",
        "¤",
        "¥",
        "¦",
        "§",
        "©",
    )

    if not any(
        marker in text
        for marker in mojibake_markers
    ):
        return text

    try:
        return text.encode("latin1").decode("utf-8")
    except (
        UnicodeEncodeError,
        UnicodeDecodeError,
    ):
        return text


def _normalize_whitespace(text: str) -> str:
    """
    Collapse repeated whitespace and trim the text.
    """

    return re.sub(r"\s+", " ", text).strip()


def _contains_malayalam(text: str) -> bool:
    """Return whether text still contains Malayalam script characters."""
    return re.search(r"[\u0D00-\u0D7F]", text) is not None


def _translate_query_with_groq(
    text: str,
    source_language: str,
) -> str:
    """Translate an untranslated Malayalam query with the shared Groq client."""
    if source_language != "ml" or not os.getenv("GROQ_API_KEY"):
        return text

    system_prompt = (
        "You are a professional marine-domain query translator. "
        "Translate Malayalam to concise English. Preserve the exact meaning. "
        "Do not answer the question, add explanations, or invent marine data. "
        "Return only the English translation. Preserve numbers, units, "
        "abbreviations, and technical terms such as SST, PFZ, and IMBL."
    )

    try:
        translated_text = _call_groq_api(
            os.environ["GROQ_API_KEY"],
            text,
            system_prompt=system_prompt,
        )
    except Exception as exc:
        logger.warning("Groq Malayalam query translation failed: %s", exc)
        return text

    if (
        not isinstance(translated_text, str)
        or not translated_text.strip()
        or _contains_malayalam(translated_text)
        or not _translation_preserves_source(text, translated_text)
    ):
        logger.warning(
            "Discarding invalid Groq Malayalam query translation"
        )
        return text

    return _normalize_whitespace(translated_text)


def translate_to_english(text: str) -> str:
    """
    Translate a supported phrase into English.

    Unknown text is returned unchanged.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    text = repair_mojibake(text)
    text = _normalize_whitespace(text)

    if not text:
        return text

    if text in TRANSLATION_MAP:
        return TRANSLATION_MAP[text]

    lowered_text = text.lower()

    if lowered_text in TRANSLATION_MAP:
        return TRANSLATION_MAP[lowered_text]

    translated_text = text

    for source_phrase, english_phrase in TRANSLATION_MAP.items():
        translated_text = translated_text.replace(
            source_phrase,
            english_phrase,
        )

    if _contains_malayalam(translated_text):
        groq_translation = _translate_query_with_groq(
            translated_text,
            "ml",
        )
        if groq_translation != translated_text:
            return groq_translation

    return translated_text


def _translate_hindi_full_response(text: str) -> str:
    """
    Translate known complete English ORCA responses into Hindi.

    Simple phrases such as:
    "Potential Fishing Zone is useful."
    are handled by the normal phrase translator instead.
    """

    normalized_text = text.strip()
    lowered_text = normalized_text.lower()

    if "strong wind warning" in lowered_text:
        return HINDI_FULL_RESPONSE_MAP["strong_wind_warning"]

    if "high wave warning" in lowered_text:
        return HINDI_FULL_RESPONSE_MAP["high_wave_warning"]

    if "cyclone warning" in lowered_text:
        return HINDI_FULL_RESPONSE_MAP["cyclone_warning"]

    if "unsafe weather warning" in lowered_text:
        return HINDI_FULL_RESPONSE_MAP["unsafe_weather_warning"]

    if "safety alert" in lowered_text:
        return HINDI_FULL_RESPONSE_MAP["return_to_shore"]

    # Only trigger the complete PFZ response for an actual
    # full-response request, not for a simple sentence.
    if (
        "potential fishing zone" in lowered_text
        and (
            "full form" in lowered_text
            or "full name" in lowered_text
            or "what is" in lowered_text
            or "stands for" in lowered_text
            or "explain" in lowered_text
            or "fishing zone information" in lowered_text
            or "recommendation" in lowered_text
            or "guarantee" in lowered_text
        )
    ):
        return HINDI_FULL_RESPONSE_MAP["pfz"]

    if (
        "sea surface temperature" in lowered_text
        and (
            "full form" in lowered_text
            or "full name" in lowered_text
            or "what is" in lowered_text
            or "stands for" in lowered_text
            or "explain" in lowered_text
        )
    ):
        return HINDI_FULL_RESPONSE_MAP["sst"]

    if (
        "international maritime boundary line" in lowered_text
        and (
            "full form" in lowered_text
            or "full name" in lowered_text
            or "what is" in lowered_text
            or "stands for" in lowered_text
            or "explain" in lowered_text
        )
    ):
        return HINDI_FULL_RESPONSE_MAP["imbl"]

    if (
        "official weather forecast" in lowered_text
        and "going to sea" in lowered_text
    ):
        return HINDI_FULL_RESPONSE_MAP["weather_forecast"]

    if (
        "before going to sea" in lowered_text
        and "life jackets" in lowered_text
    ):
        return HINDI_FULL_RESPONSE_MAP["safety_check"]

    return text


def _translate_malayalam_full_response(text: str) -> str:
    """
    Translate known complete English ORCA responses into Malayalam.
    """
    normalized_text = text.strip()
    lowered_text = normalized_text.lower()

    if "strong wind warning" in lowered_text:
        return MALAYALAM_FULL_RESPONSE_MAP["strong_wind_warning"]

    if "high wave warning" in lowered_text:
        return MALAYALAM_FULL_RESPONSE_MAP["high_wave_warning"]

    if "cyclone warning" in lowered_text:
        return MALAYALAM_FULL_RESPONSE_MAP["cyclone_warning"]

    if "unsafe weather warning" in lowered_text:
        return MALAYALAM_FULL_RESPONSE_MAP["unsafe_weather_warning"]

    if "safety alert" in lowered_text:
        return MALAYALAM_FULL_RESPONSE_MAP["return_to_shore"]

    if (
        "potential fishing zone" in lowered_text
        and (
            "full form" in lowered_text
            or "full name" in lowered_text
            or "what is" in lowered_text
            or "stands for" in lowered_text
            or "explain" in lowered_text
            or "recommendation" in lowered_text
            or "guarantee" in lowered_text
        )
    ):
        return MALAYALAM_FULL_RESPONSE_MAP["pfz"]

    if (
        "sea surface temperature" in lowered_text
        and (
            "full form" in lowered_text
            or "full name" in lowered_text
            or "what is" in lowered_text
            or "stands for" in lowered_text
            or "explain" in lowered_text
        )
    ):
        return MALAYALAM_FULL_RESPONSE_MAP["sst"]

    if (
        "international maritime boundary line" in lowered_text
        and (
            "full form" in lowered_text
            or "full name" in lowered_text
            or "what is" in lowered_text
            or "stands for" in lowered_text
            or "explain" in lowered_text
        )
    ):
        return MALAYALAM_FULL_RESPONSE_MAP["imbl"]

    if (
        "official weather forecast" in lowered_text
        and "going to sea" in lowered_text
    ):
        return MALAYALAM_FULL_RESPONSE_MAP["weather_forecast"]

    if (
        "before going to sea" in lowered_text
        and "life jackets" in lowered_text
    ):
        return MALAYALAM_FULL_RESPONSE_MAP["safety_check"]

    return text


def _translate_with_response_map(
    text: str,
    response_map: dict[str, str],
) -> str:
    """
    Apply a simple English-to-local-language response map.
    """

    translated_text = text

    phrases = sorted(
        response_map.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for english_phrase, translated_phrase in phrases:
        translated_text = re.sub(
            re.escape(english_phrase),
            translated_phrase,
            translated_text,
            flags=re.IGNORECASE,
        )

    return translated_text


def _translate_marine_phrases(
    text: str,
    target_language: str,
) -> str:
    """
    Translate complete marine phrases before individual terms.
    """

    phrase_map = MARINE_PHRASE_MAP.get(
        target_language,
        {},
    )

    translated_text = text

    phrases = sorted(
        phrase_map.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for english_phrase, translated_phrase in phrases:
        translated_text = re.sub(
            rf"\b{re.escape(english_phrase)}\b",
            translated_phrase,
            translated_text,
            flags=re.IGNORECASE,
        )

    return translated_text


def _translate_generic_response(
    text: str,
    target_language: str,
) -> str:
    """
    Translate using the available lightweight response maps.
    """

    if target_language == "hi":
        return _translate_with_response_map(
            text,
            HINDI_RESPONSE_MAP,
        )

    if target_language == "ta":
        return _translate_with_response_map(
            text,
            TAMIL_RESPONSE_MAP,
        )

    # Malayalam, Telugu, Kannada, Bengali, Marathi,
    # Gujarati, and Odia use the marine glossary.
    return text


def _is_substantially_english(text: str, target_language: str) -> bool:
    """Identify mixed or mostly-English output needing full translation."""
    if target_language != "ml":
        return False

    latin_letters = len(re.findall(r"[A-Za-z]", text))
    malayalam_letters = len(re.findall(r"[\u0D00-\u0D7F]", text))

    return (
        latin_letters >= 8
        and latin_letters > malayalam_letters
    )


def _translation_preserves_source(text: str, translated_text: str) -> bool:
    """Reject translations that lose telemetry, abbreviations, or formatting."""
    required_values = re.findall(
        r"(?<!\w)\d+(?:\.\d+)?[ \t]*(?:mg/m³|°C|knots|m|%)?",
        text,
    )

    for value in required_values:
        if value not in translated_text:
            return False

    for abbreviation in ("PFZ", "SST", "IMBL"):
        if re.search(rf"(?<!\w){abbreviation}(?!\w)", text):
            if not re.search(
                rf"(?<!\w){abbreviation}(?!\w)",
                translated_text,
            ):
                return False

    if text.count("**") != translated_text.count("**"):
        return False

    if text.count("\n\n") != translated_text.count("\n\n"):
        return False

    source_bullets = len(re.findall(r"(?m)^\s*[-*]\s+", text))
    translated_bullets = len(
        re.findall(r"(?m)^\s*[-*]\s+", translated_text)
    )
    return source_bullets == translated_bullets


def _translate_with_groq(text: str, target_language: str) -> str:
    """Translate a complete response with Groq, preserving source facts."""
    if target_language != "ml" or not os.getenv("GROQ_API_KEY"):
        return text

    system_prompt = (
        "You are a professional marine-domain translator. "
        "Translate English into Malayalam. Preserve scientific values, "
        "units, marine terminology, numerical values, abbreviations, "
        "Markdown formatting, and paragraph breaks exactly. Do not add, "
        "remove, or infer facts. Return only the translation."
    )

    try:
        translated_text = _call_groq_api(
            os.environ["GROQ_API_KEY"],
            text,
            system_prompt=system_prompt,
        )
    except Exception as exc:
        logger.warning("Groq Malayalam translation failed: %s", exc)
        return text

    if (
        not isinstance(translated_text, str)
        or not translated_text.strip()
        or not _translation_preserves_source(text, translated_text)
    ):
        logger.warning(
            "Discarding Groq Malayalam translation that changed source facts "
            "or formatting"
        )
        return text

    return translated_text.strip()


def translate_response(
    text: str,
    target_language: str = "en",
) -> str:
    """
    Translate an English response into the target language.

    Complete marine phrases are translated before individual
    glossary terms to avoid partial translations.

    Example:
        Sea Surface Temperature
    becomes:
        समुद्र की सतह का तापमान
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not isinstance(target_language, str):
        raise ValueError("Unsupported target language")

    target_language = target_language.strip().lower()
    normalized_text = text.strip()

    if not is_supported_language(target_language):
        raise ValueError(
            f"Unsupported target language: {target_language}"
        )

    if target_language == "en":
        return normalized_text

    # ---------------------------------------------------------
    # Step 1: Translate complete marine phrases first.
    #
    # This must happen before localize_glossary_terms(),
    # otherwise "Temperature" may be translated separately.
    # ---------------------------------------------------------

    phrase_translated_text = _translate_exact_marine_phrases(
        normalized_text,
        target_language,
    )

    # ---------------------------------------------------------
    # Step 2: Protect abbreviations such as PFZ, SST, and IMBL.
    # ---------------------------------------------------------

    protected_text, replacements = protect_glossary_terms(
        phrase_translated_text,
    )

    # ---------------------------------------------------------
    # Step 3: Translate known full Hindi & Malayalam responses.
    # ---------------------------------------------------------

    if target_language == "hi":
        full_translation = _translate_hindi_full_response(
            protected_text,
        )

        if full_translation != protected_text:
            return restore_glossary_terms(full_translation, replacements)

        translated_text = _translate_generic_response(
            protected_text,
            target_language,
        )
    elif target_language == "ml":
        full_translation = _translate_malayalam_full_response(
            protected_text,
        )

        if full_translation != protected_text:
            return restore_glossary_terms(full_translation, replacements)

        translated_text = _translate_generic_response(
            protected_text,
            target_language,
        )
    else:
        translated_text = _translate_generic_response(
            protected_text,
            target_language,
        )

    # ---------------------------------------------------------
    # Step 4: Localize remaining glossary terms.
    # ---------------------------------------------------------

    if isinstance(translated_text, str) and translated_text:
        translated_text = localize_glossary_terms(
            translated_text,
            target_language,
        )

    # ---------------------------------------------------------
    # Step 5: Restore abbreviations.
    # ---------------------------------------------------------

    if isinstance(translated_text, str):
        translated_text = restore_glossary_terms(
            translated_text,
            replacements,
        )

    if _is_substantially_english(translated_text, target_language):
        groq_translation = _translate_with_groq(
            normalized_text,
            target_language,
        )
        if groq_translation != normalized_text:
            translated_text = groq_translation

    return str(translated_text)


def translate_text(
    text: str,
    source_language: str = "auto",
    target_language: str = "en",
) -> dict:
    """
    Translate text and return translation metadata.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not text.strip():
        raise ValueError("text cannot be empty")

    if not isinstance(source_language, str):
        raise ValueError("Unsupported source language")

    if not isinstance(target_language, str):
        raise ValueError("Unsupported target language")

    source_language = source_language.strip().lower()
    target_language = target_language.strip().lower()

    if (
        source_language != "auto"
        and not is_supported_language(source_language)
    ):
        raise ValueError(
            f"Unsupported source language: {source_language}"
        )

    if not is_supported_language(target_language):
        raise ValueError(
            f"Unsupported target language: {target_language}"
        )

    original_text = text
    normalized_text = _normalize_whitespace(text)

    if source_language == target_language:
        return {
            "text": normalized_text,
            "translated": False,
            "fallback_used": source_language == "en",
            "original_text": original_text,
            "translated_text": normalized_text,
            "source_language": source_language,
            "target_language": target_language,
        }

    if source_language == "en":
        translated_text = translate_response(
            normalized_text,
            target_language,
        )

        translated = translated_text != normalized_text

        return {
            "text": translated_text,
            "translated": translated,
            "fallback_used": not translated,
            "original_text": original_text,
            "translated_text": translated_text,
            "source_language": source_language,
            "target_language": target_language,
        }

    if target_language == "en":
        translated_text = translate_to_english(
            normalized_text,
        )

        translated = translated_text != normalized_text

        return {
            "text": translated_text,
            "translated": translated,
            "fallback_used": not translated,
            "original_text": original_text,
            "translated_text": translated_text,
            "source_language": source_language,
            "target_language": target_language,
        }

    # For non-English to non-English translation, use glossary
    # localization while preserving the original text if no
    # glossary term is found.
    translated_text = localize_glossary_terms(
        normalized_text,
        target_language,
    )

    translated = translated_text != normalized_text

    return {
        "text": translated_text,
        "translated": translated,
        "fallback_used": not translated,
        "original_text": original_text,
        "translated_text": translated_text,
        "source_language": source_language,
        "target_language": target_language,
    }
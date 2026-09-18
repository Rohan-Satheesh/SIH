"""
ORCA Language Detector

Detects English and supported Indian languages (Malayalam, Tamil, Telugu, Hindi, Kannada, Bengali, Odia, Gujarati, Marathi).
Uses Unicode script ranges with langdetect fallback and safeguards for short maritime queries.
"""

from typing import Optional, Dict, Any
import re

try:
    from langdetect import DetectorFactory, detect_langs
    DetectorFactory.seed = 0
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False

SUPPORTED_LANGUAGES = {
    "en", "hi", "ta", "ml", "te", "kn", "or", "bn", "mr", "gu"
}

ENGLISH_WORDS = {
    "a", "am", "an", "and", "are", "can", "check", "do", "fishing", "for",
    "hello", "help", "how", "is", "near", "please", "safe", "sea", "the",
    "to", "tomorrow", "what", "when", "where", "which", "why", "wind", "weather",
    "port", "boat", "tide", "wave", "catch", "ocean", "kochi", "route"
}

def _contains_indian_script(text: str) -> bool:
    """Check whether text contains characters from common Indian writing systems."""
    indian_script_pattern = (
        r"[\u0900-\u097F"   # Devanagari: Hindi, Marathi
        r"\u0980-\u09FF"   # Bengali
        r"\u0B00-\u0B7F"   # Odia
        r"\u0B80-\u0BFF"   # Tamil
        r"\u0C00-\u0C7F"   # Telugu
        r"\u0C80-\u0CFF"   # Kannada
        r"\u0D00-\u0D7F]"  # Malayalam
    )
    return re.search(indian_script_pattern, text) is not None

def _detect_by_script(text: str) -> Optional[str]:
    """Fast deterministic detection via Unicode code block."""
    if re.search(r'[\u0D00-\u0D7F]', text):
        return "ml"
    if re.search(r'[\u0B80-\u0BFF]', text):
        return "ta"
    if re.search(r'[\u0C00-\u0C7F]', text):
        return "te"
    if re.search(r'[\u0900-\u097F]', text):
        return "hi"
    if re.search(r'[\u0C80-\u0CFF]', text):
        return "kn"
    if re.search(r'[\u0980-\u09FF]', text):
        return "bn"
    if re.search(r'[\u0B00-\u0B7F]', text):
        return "or"
    return None

def _looks_like_english(text: str) -> bool:
    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    return len(words.intersection(ENGLISH_WORDS)) >= 1 if words else False

def detect_language_details(text: str) -> Dict[str, Any]:
    """
    Detailed language detector returning structured diagnostic metadata.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    text = text.strip()
    if not text:
        return {
            "language_code": None,
            "confidence": 0.0,
            "is_mixed_with_english": False,
            "low_confidence": True,
        }

    # Direct script detection
    script_lang = _detect_by_script(text)
    if script_lang:
        is_mixed = _looks_like_english(text)
        return {
            "language_code": script_lang,
            "confidence": 0.98,
            "is_mixed_with_english": is_mixed,
            "low_confidence": False,
        }

    # English safeguard
    if _looks_like_english(text):
        return {
            "language_code": "en",
            "confidence": 0.95,
            "is_mixed_with_english": False,
            "low_confidence": False,
        }

    # Optional statistical langdetect
    if HAS_LANGDETECT:
        try:
            detected = detect_langs(text)
            if detected:
                best = detected[0]
                lang_code = best.lang.lower()
                prob = float(best.prob)
                if lang_code in SUPPORTED_LANGUAGES and prob >= 0.50:
                    return {
                        "language_code": lang_code,
                        "confidence": prob,
                        "is_mixed_with_english": _looks_like_english(text) and lang_code != "en",
                        "low_confidence": False,
                    }
        except Exception:
            pass

    return {
        "language_code": "en",
        "confidence": 0.70,
        "is_mixed_with_english": False,
        "low_confidence": True,
    }

def detect_language(text: str, default_lang: Optional[str] = "ML") -> str:
    """
    Detects language and returns 2-letter uppercase language code (e.g. 'ML', 'EN', 'HI', 'TA', 'TE')
    for seamless compatibility across server and agents.
    """
    if not text:
        return (default_lang or "ML").upper()

    details = detect_language_details(text)
    code = details.get("language_code")
    if code:
        return code.upper()
    return (default_lang or "EN").upper()
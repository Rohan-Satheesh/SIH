"""
NeerMitra / ORCA NLP Subsystem

Provides:
- Language detection (Unicode scripts, langdetect, Hinglish)
- Intent classification (Sentence-transformers & regex fallback)
- Marine glossary expansion & translation
- RAG document retrieval & context formatting
- Voice STT & TTS interfaces
- Unified NLP pipeline (orca_service.process_query)
"""

from nlp.detection.language_detector import detect_language, detect_language_details
from nlp.detection.intent_classifier import classify_intent, classify_fisher_intent
from nlp.translation.marine_glossary import expand_terms, MARINE_GLOSSARY
from nlp.translation.translator import translate_to_english, translate_response
from nlp.rag.rag_pipeline import get_relevant_context
from nlp.orca_service import process_query

__all__ = [
    "detect_language",
    "detect_language_details",
    "classify_intent",
    "classify_fisher_intent",
    "expand_terms",
    "MARINE_GLOSSARY",
    "translate_to_english",
    "translate_response",
    "get_relevant_context",
    "process_query",
]

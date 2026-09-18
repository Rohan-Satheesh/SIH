"""
nlp/detection/intent_classifier.py

Operational Intent Classification Engine for NeerMitra / ORCA.
Supports sentence-transformers embedding similarity with robust semantic/keyword fallbacks.
"""

from typing import Dict, Any, Optional
import re
import logging

logger = logging.getLogger("neermitra.nlp.intent")

# Define structured semantic definitions instead of simple keyword arrays
INTENT_DEFINITIONS = {
    "TERMINOLOGY_EXPLANATION": {
        "description": "User is asking for definitions, meaning, or explanation of terms like PFZ, SST, IMBL, Chlorophyll.",
        "keywords": ["what is", "meaning", "define", "explain", "stand for", "kya hai", "samjhao", "enthaanu", "enthanu", "definition"],
        "examples": [
            "what is pfz",
            "what does pfz mean",
            "explain potential fishing zone",
            "what is sst",
            "what is imbl",
            "explain chlorophyll concentration",
            "is pfz a guarantee of fish",
            "how does pfz work",
            "what is wave height",
            "pfz kya hai",
            "marine terms and meanings"
        ]
    },
    "PFZ_LOCATION": {
        "description": "User is asking where to find fish, potential fishing zones, fishing spots, or hotspots.",
        "keywords": ["where", "find fish", "catch fish", "spots", "location", "nearest pfz", "shoals", "hotspots", "chakar", "meen"],
        "examples": [
            "where is the nearest potential fishing zone",
            "where can I find fish today",
            "show me good fishing spots nearby",
            "location of fish shoals",
            "where are the fishing zones today"
        ]
    },
    "WEATHER_FORECAST": {
        "description": "User is asking about weather conditions, waves, wind, tides, storm, cyclone, or rain.",
        "keywords": ["weather", "wave", "wind", "storm", "cyclone", "rain", "swell", "tide", "forecast", "temperature", "climate", "mausam"],
        "examples": [
            "what is the wind speed today",
            "will it rain tomorrow",
            "wave height forecast for this week",
            "tide levels near the coast",
            "current sea condition"
        ]
    },
    "SAFETY_CHECK": {
        "description": "User is asking if it is safe to go to sea, safety guidelines, warnings, or emergency.",
        "keywords": ["safe", "danger", "warning", "emergency", "sos", "rescue", "help", "life jacket", "should i go", "can i go", "suraksha"],
        "examples": [
            "is it safe to go fishing today",
            "should I go to sea tomorrow",
            "is the weather safe for fishing",
            "any warning against going to sea",
            "emergency safety guidelines"
        ]
    },
    "GEOFENCE_CHECK": {
        "description": "User is asking about maritime boundaries, borders, IMBL, or distance to restricted waters.",
        "keywords": ["boundary", "border", "imbl", "sri lanka", "restricted", "limit", "geofence", "cross", "distance", "mpa"],
        "examples": [
            "am I close to the Sri Lanka maritime boundary",
            "how far am I from the international border",
            "will I cross into restricted waters",
            "imbl border distance"
        ]
    },
    "SST_QUERY": {
        "description": "User is asking specifically for current sea surface temperature readings.",
        "keywords": ["sst", "sea surface temperature", "water temperature", "temperature of sea"],
        "examples": [
            "current sea surface temperature near kochi",
            "what is the water temperature today",
            "live sst reading at my location"
        ]
    },
    "CHLOROPHYLL_QUERY": {
        "description": "User is asking specifically about chlorophyll or ocean productivity.",
        "keywords": ["chlorophyll", "chlorophyll-a", "productivity"],
        "examples": [
            "current chlorophyll concentration near port",
            "chlorophyll map today",
            "live ocean productivity reading"
        ]
    },
    "ROUTE_RISK": {
        "description": "User is asking about routes, paths, navigation, or safest way to a destination.",
        "keywords": ["route", "path", "transit", "waypoint", "voyage", "navigation", "way"],
        "examples": [
            "safest route from Mangalore avoiding high waves",
            "plan a route to the fishing zone",
            "risk along my route to the harbor"
        ]
    },
    "GENERAL_CONVERSATION": {
        "description": "Greetings, thanks, or general pleasantries.",
        "keywords": ["hello", "hi", "hey", "good morning", "thank you", "thanks", "namaste", "namaskaram"],
        "examples": [
            "hello",
            "good morning",
            "thank you",
            "thanks for your help"
        ]
    },
    "CLARIFICATION": {
        "description": "Follow-up questions or requests for clarification.",
        "keywords": ["how", "why", "what about", "and", "can you explain further", "tell me more", "how is it calculated"],
        "examples": [
            "how is it calculated?",
            "can you explain further?",
            "what about tomorrow?",
            "why does it matter?"
        ]
    }
}

CONFIDENCE_THRESHOLD = 0.55

_MODEL = None
_INTENT_EMBEDDINGS = None

def _get_model_and_embeddings():
    global _MODEL, _INTENT_EMBEDDINGS
    if _MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
            _INTENT_EMBEDDINGS = {
                intent: _MODEL.encode(data["examples"], convert_to_tensor=True)
                for intent, data in INTENT_DEFINITIONS.items()
            }
        except Exception as e:
            logger.warning(f"sentence_transformers not loaded, will use semantic fallback: {e}")
            _MODEL = False
    return _MODEL, _INTENT_EMBEDDINGS

def _semantic_keyword_classify(text: str) -> Dict[str, Any]:
    """Robust semantic scoring fallback when sentence-transformers is unavailable."""
    lower = text.lower().strip()
    
    best_intent = "GENERAL_CONVERSATION"
    best_score = 0.0
    
    # Check exact terminology matches (highest priority)
    exact_terms = {
        "pfz": "TERMINOLOGY_EXPLANATION",
        "potential fishing zone": "TERMINOLOGY_EXPLANATION",
        "sst": "TERMINOLOGY_EXPLANATION",
        "sea surface temperature": "TERMINOLOGY_EXPLANATION",
        "imbl": "TERMINOLOGY_EXPLANATION",
        "chlorophyll": "TERMINOLOGY_EXPLANATION",
        "eez": "TERMINOLOGY_EXPLANATION"
    }
    
    if lower in exact_terms:
        return {"intent": exact_terms[lower], "confidence": 0.95, "low_confidence": False}

    # Score each intent based on keyword overlap
    words = set(re.findall(r'\b\w+\b', lower))
    
    for intent, data in INTENT_DEFINITIONS.items():
        score = 0.0
        for kw in data["keywords"]:
            if kw in lower:
                # Longer phrases get higher weight
                score += len(kw.split()) * 0.3
                
        if score > best_score:
            best_score = score
            best_intent = intent
            
    # Normalize score somewhat arbitrarily for fallback
    confidence = min(0.9, best_score / 2.0)
    
    if confidence < 0.2:
        return {"intent": "UNSUPPORTED", "confidence": confidence, "low_confidence": True}
        
    return {"intent": best_intent, "confidence": confidence, "low_confidence": confidence < CONFIDENCE_THRESHOLD}

def classify_intent(text: str) -> dict:
    """
    Classifies a user query into an operational intent category using a hierarchical approach.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not text.strip():
        return {
            "intent": "GENERAL_CONVERSATION",
            "confidence": 0.0,
            "low_confidence": True,
        }

    lower = text.lower()

    # Early exit for explicit SOS/Emergencies
    if re.search(r'\b(sos|mayday|help|emergency|rescue)\b', lower):
        return {"intent": "SAFETY_CHECK", "confidence": 0.99, "low_confidence": False}

    model, embeddings = _get_model_and_embeddings()
    if model and embeddings:
        try:
            from sentence_transformers import util
            query_embedding = model.encode(text, convert_to_tensor=True)
            best_intent = None
            best_score = -1.0

            for intent, example_embeddings in embeddings.items():
                similarities = util.cos_sim(query_embedding, example_embeddings)
                max_similarity = similarities.max().item()
                if max_similarity > best_score:
                    best_score = max_similarity
                    best_intent = intent

            if best_score < 0.3:
                # Very low confidence across all marine intents
                return {"intent": "UNSUPPORTED", "confidence": float(best_score), "low_confidence": True}

            return {
                "intent": best_intent,
                "confidence": float(best_score),
                "low_confidence": best_score < CONFIDENCE_THRESHOLD,
            }
        except Exception as e:
            logger.error(f"Error during sentence_transformers classification: {e}")

    # Fallback to robust keyword scoring
    return _semantic_keyword_classify(text)

def classify_fisher_intent(text: str) -> Dict[str, Any]:
    return classify_intent(text)
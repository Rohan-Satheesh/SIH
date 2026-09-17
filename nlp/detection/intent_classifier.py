"""
nlp/detection/intent_classifier.py

Operational Intent Classification Engine for NeerMitra / ORCA.
Supports sentence-transformers embedding similarity with zero-latency regex/keyword fallbacks.
"""

from typing import Dict, Any, Optional
import re
import logging

logger = logging.getLogger("neermitra.nlp.intent")

INTENT_EXAMPLES = {
    "TERMINOLOGY_EXPLANATION": [
        "what is pfz",
        "what does pfz mean",
        "explain potential fishing zone",
        "what is sst",
        "what does sst stand for",
        "what is imbl",
        "explain chlorophyll concentration",
        "is pfz a guarantee of fish",
        "how does pfz work",
        "what is wave height",
        "what is eez",
        "pfz kya hai",
        "pfz enthaanu",
        "marine terms and meanings",
    ],
    "PFZ_LOCATION": [
        "where is the nearest potential fishing zone",
        "where can I find fish today",
        "show me good fishing spots nearby",
        "location of fish shoals",
        "best area to catch fish right now",
        "where are the fishing zones today",
        "where to catch tuna today",
    ],
    "WEATHER_FORECAST": [
        "what is the wind speed today",
        "will it rain tomorrow",
        "wave height forecast for this week",
        "tide levels near the coast",
        "weather conditions at sea",
        "current sea condition",
        "wave conditions today",
    ],
    "SAFETY_CHECK": [
        "is it safe to go fishing today",
        "should I go to sea tomorrow",
        "can I venture into the sea this evening",
        "is the weather safe for fishing",
        "any warning against going to sea",
        "safety checklist for fishing boat",
        "emergency safety guidelines",
    ],
    "GEOFENCE_CHECK": [
        "am I close to the Sri Lanka maritime boundary",
        "how far am I from the international border",
        "distance to the maritime boundary line",
        "will I cross into restricted waters",
        "check if I am near the boundary",
        "imbl border distance",
    ],
    "SST_QUERY": [
        "current sea surface temperature near kochi",
        "what is the water temperature today",
        "live sst reading at my location",
    ],
    "CHLOROPHYLL_QUERY": [
        "current chlorophyll concentration near port",
        "chlorophyll map today",
        "live ocean productivity reading",
    ],
    "ROUTE_RISK": [
        "safest route from Mangalore avoiding high waves",
        "plan a route to the fishing zone",
        "which path should I take to avoid rough seas",
        "risk along my route to the harbor",
        "best route considering the weather",
    ],
    "GENERAL_CONVERSATION": [
        "hello",
        "hi",
        "hey",
        "good morning",
        "thank you",
        "thanks for your help",
        "namaste",
        "namaskaram",
    ],
    "UNSUPPORTED": [
        "how to bake a cake",
        "who is the president",
        "what is the stock price of google",
        "write a python script for sorting",
        "recommend a movie to watch",
    ],
}

CONFIDENCE_THRESHOLD = 0.5

_MODEL = None
_INTENT_EMBEDDINGS = None

def _get_model_and_embeddings():
    global _MODEL, _INTENT_EMBEDDINGS
    if _MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
            _INTENT_EMBEDDINGS = {
                intent: _MODEL.encode(examples, convert_to_tensor=True)
                for intent, examples in INTENT_EXAMPLES.items()
            }
        except Exception as e:
            logger.debug(f"sentence_transformers not loaded, using regex fallback: {e}")
            _MODEL = False
    return _MODEL, _INTENT_EMBEDDINGS

def _keyword_classify(text: str) -> Dict[str, Any]:
    """Fast regex and keyword intent classifier across English and Indian languages."""
    lower = text.lower().strip()

    # 1. Casual greetings & general conversation
    if re.fullmatch(r'(hi|hello|hey|hii|good morning|good evening|good afternoon|thanks|thank you|namaste|namaskaram|നമസ്കാരം|നന്ദി|नमस्ते|धन्यवाद)', lower):
        return {"intent": "GENERAL_CONVERSATION", "confidence": 0.98, "low_confidence": False}

    # 2. Safety emergencies / SOS
    if re.search(r'\b(sos|mayday|help|emergency|rescue|breakdown|sink|distress)\b', lower) or \
       re.search(r'(അപകടം|രക്ഷിക്കൂ|എഞ്ചിൻ|തകരാർ|സഹായം|बचाओ|मदद)', lower):
        return {"intent": "SAFETY_CHECK", "confidence": 0.95, "low_confidence": False}

    # 3. Educational & Terminology questions (What is PFZ, SST, IMBL, meaning, definition, explain, guarantee)
    definition_regex = r'\b(what is|what are|what does|meaning of|define|definition|explain|tell me about|how does|is pfz a guarantee|guarantee of fish|kya hai|kya hota|samjhao|batao|matlab|enthaanu|enthanu|enth)\b'
    is_def_pattern = bool(re.search(definition_regex, lower)) or \
                     bool(re.search(r'(എന്താണ്|അർത്ഥം|വിശദീകരിക്കുക|क्या है|क्या होता है|समझाओ)', lower))

    # Bare acronyms or terms as single token queries (e.g. "pfz", "sst", "imbl", "chlorophyll")
    is_bare_term = lower in {"pfz", "sst", "imbl", "eez", "chlorophyll", "chlorophyll-a", "potential fishing zone", "sea surface temperature"}

    if is_def_pattern or is_bare_term or "guarantee" in lower:
        return {"intent": "TERMINOLOGY_EXPLANATION", "confidence": 0.95, "low_confidence": False}

    # 4. Geofence / Boundary / Border / IMBL queries
    if re.search(r'\b(boundary|border|imbl|sri lanka|line|restricted|limit|geofence|mpa|transgression|cross.*border)\b', lower) or \
       re.search(r'(അതിർത്തി|സമുദ്ര പരിധി|വിലക്ക്|सीमा|बॉर्डर)', lower):
        return {"intent": "GEOFENCE_CHECK", "confidence": 0.92, "low_confidence": False}

    # 5. Live PFZ / Fish location queries (Where are fish, find fish today, spots, shoals)
    if re.search(r'\b(where.*fish|where.*pfz|find fish|fish spots|fishing spots|catch fish today|nearest pfz|locate fish|shoals|hotspots)\b', lower) or \
       re.search(r'(മീൻ എവിടെ|ചാകര എവിടെ|മത്സ്യ ലഭ്യത|मछली कहाँ|मछली पकड़ने की जगह)', lower):
        return {"intent": "PFZ_LOCATION", "confidence": 0.92, "low_confidence": False}

    # 6. Route & navigation queries
    if re.search(r'\b(route|path|transit|waypoint|voyage|navigation path|safest way)\b', lower) or \
       re.search(r'(വഴി|റൂട്ട്|मार्ग|रास्ता)', lower):
        return {"intent": "ROUTE_RISK", "confidence": 0.90, "low_confidence": False}

    # 7. Safety / venture check ("is it safe to go", "can i go to sea", "safety tips")
    if re.search(r'\b(is it safe|should i go|can i go|safe to venture|safe for fishing|safety checklist|life jacket|safety advice)\b', lower) or \
       re.search(r'(കടലിൽ പോകാൻ സുരക്ഷിതമാണോ|സുരക്ഷ|सुरक्षित है|सुरक्षा)', lower):
        return {"intent": "SAFETY_CHECK", "confidence": 0.92, "low_confidence": False}

    # 8. Weather, wave, wind, cyclone, tide forecast
    if re.search(r'\b(weather|wave|waves|wind|winds|storm|cyclone|rain|swell|sea condition|tide|forecast|temperature)\b', lower) or \
       re.search(r'(കാലാവസ്ഥ|തിരമാല|കാറ്റ്|മഴ|കടൽ അവസ്ഥ|मौसम|हवा|लहर)', lower):
        return {"intent": "WEATHER_FORECAST", "confidence": 0.91, "low_confidence": False}

    # 9. Generic fish keywords -> PFZ Location
    if re.search(r'\b(fish|fishing|catch|tuna|mackerel|sardine)\b', lower) or \
       re.search(r'(മീൻ|മത്സ്യം|मछली)', lower):
        return {"intent": "PFZ_LOCATION", "confidence": 0.85, "low_confidence": False}

    # 10. Check for unsupported non-marine queries
    unsupported_indicators = [
        "cake", "bake", "recipe", "movie", "song", "actor", "cricket", "football",
        "stock", "share price", "crypto", "bitcoin", "code", "python", "javascript",
        "president", "prime minister", "homework", "car", "flight"
    ]
    if any(ind in lower for ind in unsupported_indicators):
        return {"intent": "UNSUPPORTED", "confidence": 0.90, "low_confidence": False}

    return {"intent": "TERMINOLOGY_EXPLANATION", "confidence": 0.70, "low_confidence": False}

def classify_intent(text: str) -> dict:
    """
    Classifies a user query into an operational intent category.
    Returns:
        {
            "intent": str,
            "confidence": float,
            "low_confidence": bool
        }
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not text.strip():
        return {
            "intent": "GENERAL_CONVERSATION",
            "confidence": 0.0,
            "low_confidence": True,
        }

    # First run keyword classification for deterministic, high-confidence domain patterns
    kw_result = _keyword_classify(text)
    if kw_result.get("confidence", 0) >= 0.85:
        return kw_result

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

            return {
                "intent": best_intent,
                "confidence": best_score,
                "low_confidence": best_score < CONFIDENCE_THRESHOLD,
            }
        except Exception:
            pass

    return kw_result

def classify_fisher_intent(text: str) -> Dict[str, Any]:
    return classify_intent(text)
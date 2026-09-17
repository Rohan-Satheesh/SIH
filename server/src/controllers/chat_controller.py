import re
import logging
from typing import Optional
from shared.schemas.chat_schema import ChatRequest, CopilotResponse
from nlp.detection.language_detector import detect_language
from nlp.orca_service import process_query
from nlp.llm.gemini_fallback import clean_rag_leakage
from agents.orchestrator.graph import run_marine_agent
from server.src.config.database import get_db_engine

logger = logging.getLogger("neermitra.chat_controller")

def is_casual_message(message: str) -> bool:
    normalized = re.sub(r"[^a-z\s']", " ", message.lower()).strip()
    return normalized in {
        "hi", "hello", "hey", "hii", "hiii", "good morning",
        "good afternoon", "good evening", "thanks", "thank you",
        "നമസ്കാരം", "ഹലോ", "നന്ദി", "नमस्ते", "धन्यवाद"
    }

def casual_response(message: str, language: str = "EN") -> CopilotResponse:
    normalized = message.strip().lower()
    is_thanks = normalized in {"thanks", "thank you", "നന്ദി", "धन्यवाद"}
    
    if language == "ML":
        text = "സ്വാഗതം! കടൽ കാലാവസ്ഥ, മത്സ്യ ലഭ്യത മേഖലകൾ (PFZ), സമുദ്ര അതിർത്തികൾ എന്നിവയെക്കുറിച്ച് ചോദിക്കാം." if is_thanks else \
               "നമസ്കാരം! തത്സമയ കടൽ കാലാവസ്ഥ, മത്സ്യ ലഭ്യത മേഖലകൾ, സുരക്ഷാ മാർഗ്ഗനിർദ്ദേശങ്ങൾ എന്നിവയിൽ ഞാൻ സഹായിക്കാം. എന്താണ് അറിയേണ്ടത്?"
    elif language == "HI":
        text = "आपका स्वागत है! आप समुद्री मौसम, मत्स्य क्षेत्र (PFZ), या सीमा सुरक्षा के बारे में पूछ सकते हैं।" if is_thanks else \
               "नमस्ते! मैं समुद्री मौसम, संभावित मत्स्य क्षेत्र (PFZ) और सुरक्षा सलाह में आपकी सहायता कर सकता हूँ। आप क्या जानना चाहते हैं?"
    else:
        text = "You're welcome! Ask me about sea conditions, fishing zones (PFZ), boundaries, or route safety." if is_thanks else \
               "Hello! I can help with live sea conditions, fishing zones, maritime boundaries, and route safety. What would you like to check?"

    return CopilotResponse(
        text=text,
        confidence=100,
        location="",
        conditions=[],
        risk="LOW",
        agents_invoked=["CasualRouter"],
    )

def is_live_telemetry_or_spatial_query(query: str) -> bool:
    """
    Checks if query requires real-time GPS coordinate math, live satellite wave/wind feeds,
    or map waypoint routing rather than general educational knowledge.
    """
    q = query.lower()

    # Check for specific ports, sectors, or coordinates
    location_names = [
        "kochi", "cochin", "കൊച്ചി", "munambam", "മുനമ്പം", "alappuzha", "ആലപ്പുഴ",
        "goa", "mumbai", "mangalore", "chennai", "vizag", "visakhapatnam",
        "rameswaram", "kutch", "gulf of kutch", "gujarat", "odisha", "paradip",
        "bengal", "sundarbans", "kollam", "kozhikode", "trivandrum", "veraval", "porbandar"
    ]
    has_location = any(loc in q for loc in location_names)

    live_patterns = [
        r'\b(nearby|nearest|closest|distance|bearing|coordinate|coordinates|lat|lon|waypoint|route to)\b',
        r'\b(how far|where is|where are|locate|directions? to|show on map|near me)\b',
        r'\b(waves?|winds?|weather|swells?|tides?|sea conditions?|wave conditions?|wave height|wind speed|live conditions?|current weather|forecast|safe to venture|is it safe|can i go|safe to travel|safe to fish)\b',
        r'\b(fishing zones?|pfz zones?|fish zones?|find fish|where to fish|catch fish|fishing spots?|hotspots?)\b',
        r'(എവിടെയാണ്|എത്ര ദൂരം|ഏറ്റവും അടുത്ത|കി.മീ|നോട്ടിക്കൽ മൈൽ|കാലാവസ്ഥ|തിരമാല|കാറ്റ്|മീൻ ലഭ്യത|ചാകര)',
        r'(कहाँ है|कितनी दूर|नजदीकी|दूरी|लहरों की ऊंचाई|लहर|हवा|मौसम|मछली पकड़ने का क्षेत्र|मछली कहाँ)'
    ]
    has_live_pattern = any(re.search(pat, q) for pat in live_patterns)

    # Location + live marine question -> Always route to Agent Swarm
    if has_location and has_live_pattern:
        return True

    # Bare acronyms or single-term glossary lookups
    bare_terms = {"pfz", "sst", "imbl", "eez", "chlorophyll", "wave height", "wind speed", "potential fishing zone", "sea surface temperature"}
    if q.strip() in bare_terms:
        return False

    # If it is explicitly asking for a definition, explanation, or general knowledge without a specific live location, prioritize Tier 1 NLP
    definition_markers = [
        "what is", "what are", "what's", "what does", "explain", "meaning", "define", "definition",
        "tell me about", "kya hai", "kya h", "kya hota", "samjhao", "batao", "kise kehte",
        "kaisa hota", "aratham", "matlab", "meaning of", "info on", "information about",
        "terms", "guidelines", "safety tips", "rules", "rule", "regulations", "guarantee",
        "how does", "how can i use",
        "എന്താണ്", "അർത്ഥം", "വിശദീകരിക്കുക", "എന്താണ് ഉദ്ദേശിക്കുന്നത്",
        "क्या है", "क्या होता है", "बताओ", "समझाओ", "अर्थ", "नियम",
        "என்ன", "விளக்கு", "பொருள்", "ఏమిటి", "వివరించు"
    ]
    if any(marker in q for marker in definition_markers) and not has_location:
        return False

    return has_live_pattern or has_location

def handle_chat_request(req: ChatRequest) -> CopilotResponse:
    """
    3-Tier Processing Pipeline:
    Tier 1 (Top Priority): Friend's ORCA NLP (Definitions, glossary, marine alerts, RAG knowledge)
    Tier 2: NeerMitra Agent Swarm (Live satellite weather, PostGIS distance & EEZ checking, GPS routing)
    Tier 3: AI / LLM Fallback (Gemini API with GEMINI_API_KEY or deterministic fallback)
    """
    requested_lang = None
    if req.context and isinstance(req.context, dict):
        requested_lang = req.context.get("language")

    detected_lang = detect_language(req.message, requested_lang)

    # Check casual greeting
    if is_casual_message(req.message):
        return casual_response(req.message, detected_lang)

    # -------------------------------------------------------------------------
    # TIER 1: Prioritize Friend's NLP Engine
    # (Processes definitions, glossary terms, marine alerts, and RAG knowledge)
    # -------------------------------------------------------------------------
    if not is_live_telemetry_or_spatial_query(req.message):
        try:
            orca_result = process_query(req.message)
            answer = orca_result.get("answer") or orca_result.get("final_answer") or orca_result.get("english_answer")
            
            if answer:
                answer = clean_rag_leakage(answer)
                fallback_needles = ["could not find enough information", "not found"]
                is_generic_fallback = any(needle in answer.lower() for needle in fallback_needles)

                if not is_generic_fallback and len(answer.strip()) > 15:
                    spatial_payload = {}
                    if orca_result.get("evidence"):
                        spatial_payload["rag_evidence"] = orca_result.get("evidence")

                    return CopilotResponse(
                        text=answer,
                        confidence=95,
                        location="",
                        conditions=[],
                        risk="LOW",
                        agents_invoked=["OrcaNLP", "MarineRAGKnowledgeAgent"],
                        spatial_payload=spatial_payload
                    )
        except Exception as e:
            logger.debug(f"Tier 1 ORCA NLP pass-through: {e}")

    # -------------------------------------------------------------------------
    # TIER 2 & 3: NeerMitra Agent Swarm & AI Engine
    # (Live GPS math, PostGIS EEZ boundaries, Open-Meteo telemetry, LLM fallback)
    # -------------------------------------------------------------------------
    engine = get_db_engine()
    try:
        agent_result = run_marine_agent(
            engine,
            req.message,
            detected_lang,
            context=req.context,
            session_id=req.session_id,
            history=req.history
        )
        return CopilotResponse(**agent_result)
    except Exception as exc:
        logger.error(f"Agent execution error: {exc}")
        return CopilotResponse(
            text="Live marine intelligence is temporarily unavailable. Safe navigation advised.",
            confidence=0,
            location="",
            conditions=[],
            risk="LOW",
            agents_invoked=[],
        )

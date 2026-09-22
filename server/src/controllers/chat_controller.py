import re
import logging
from typing import Optional
from shared.schemas.chat_schema import ChatRequest, CopilotResponse
from nlp.detection.language_detector import detect_language
from nlp.llm.groq_client import clean_rag_leakage
from agents.orchestrator.graph import run_marine_agent
from server.src.config.database import get_db_engine
from server.src.services.session_manager import upsert_session

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

def handle_chat_request(req: ChatRequest) -> CopilotResponse:
    """
    Main Processing Pipeline:
    Routes all queries to the NeerMitra Agent Swarm (LangGraph)
    for planning, intent extraction, and execution.
    """
    requested_lang = req.language

    if not requested_lang and req.context and isinstance(req.context, dict):
        requested_lang = req.context.get("language")

    detected_lang = detect_language(req.message, requested_lang)

    logger.info(
        "Language resolution: requested_lang=%r detected_lang=%r req.language=%r",
        requested_lang,
        detected_lang,
        req.language,
    )

    # Best-effort durable session record (PRD R2-C09). Never affects the
    # response — upsert_session() swallows and logs any failure internally.
    upsert_session(
        session_id=req.session_id,
        language=detected_lang,
        vessel_type=req.vessel_type,
        location=req.location,
        last_query=req.message,
    )

    # Check casual greeting
    if is_casual_message(req.message):
        return casual_response(req.message, detected_lang)

    # Route EVERYTHING ELSE to NeerMitra Agent Swarm
    engine = get_db_engine()

    try:
        logger.info(
            "Chat controller message: repr=%r unicode_points=%s",
            req.message,
            [hex(ord(ch)) for ch in req.message],
        )

        agent_result = run_marine_agent(
            engine,
            req.message,
            detected_lang,
            context=req.context,
            session_id=req.session_id,
            history=req.history,
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
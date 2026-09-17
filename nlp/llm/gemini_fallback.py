"""
nlp/llm/gemini_fallback.py

Intelligent Marine Response Synthesis Engine for NeerMitra.
Provides contextual, fisherman-friendly response generation via Gemini LLM
with a robust, natural deterministic fallback synthesizer.
Zero leakage of chunk IDs, document metadata, or raw RAG dumps.
"""

import os
import re
import logging
from typing import Optional, List, Union
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("neermitra.nlp.llm")

# System prompt defining NeerMitra persona and fisherman-friendly guidelines
NEERMITRA_SYSTEM_PROMPT = """You are NeerMitra, an intelligent, conversational marine assistant created for coastal fishermen in India.
Your mission is to provide simple, clear, practical, and highly helpful answers in conversational language.

Guidelines:
1. Speak directly, respectfully, and clearly to the fisherman.
2. When explaining PFZ (Potential Fishing Zone), clearly state that PFZ is a scientific advisory based on Sea Surface Temperature (SST) and chlorophyll concentration, NOT an absolute guarantee of fish. Emphasize that fishermen should always check weather conditions, boat capacity, and safety warnings before heading out.
3. Keep answers concise, practical, and free of unnecessary technical jargon or raw academic text.
4. NEVER output raw document headers, chunk IDs, source filenames (e.g., marine_terms.txt), or internal system information.
5. If answering in a regional language (like Malayalam or Hindi), preserve standard marine terms (PFZ, SST, IMBL, Chlorophyll) accurately.
"""

def clean_rag_leakage(text: str) -> str:
    """
    Guardrail to ensure no raw document markers, chunk IDs, or internal file paths leak to user.
    """
    if not text:
        return ""
    
    cleaned = text
    # If the LLM hallucinates the exact metadata block:
    # [Document 1] Source: marine_terms.txt Section: General Chunk ID: marine_terms_0 Content:
    cleaned = re.sub(r'\[Document\s+\d+\]\s*Source:.*?Chunk\s*ID:\s*\S+\s*Content:\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Also strip isolated occurrences safely:
    cleaned = re.sub(r'\[Document\s+\d+\]\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Chunk\s*ID:\s*\S+\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Source:\s*\S+\.(txt|pdf|csv|json)\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Remove 'Content: ' if it appears at the start of a sentence or isolated
    cleaned = re.sub(r'\bContent:\s*', '', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    return cleaned

def synthesize_deterministic_fallback(
    query: str,
    context_facts: Union[List[str], str] = "",
    language: str = "en",
    intent: str = "TERMINOLOGY_EXPLANATION"
) -> str:
    """
    Intelligent, deterministic natural language generator when LLM API is unavailable.
    Provides natural, human-like answers for marine queries without raw text dumps.
    """
    q = query.lower().strip()
    facts_str = context_facts if isinstance(context_facts, str) else "\n".join(context_facts)
    facts_str = clean_rag_leakage(facts_str)

    # 1. Unsupported non-marine questions
    if intent == "UNSUPPORTED":
        return (
            "I am NeerMitra, your marine and fishing assistant. I specialize in ocean conditions, "
            "potential fishing zones (PFZ), sea surface temperature, weather safety, and maritime boundary navigation. "
            "Please ask me questions related to the sea, weather, or fishing."
        )

    # 2. PFZ / Potential Fishing Zone Questions
    if any(k in q for k in ["pfz", "potential fishing zone", "fishing zone"]) or intent == "PFZ_LOCATION":
        if "guarantee" in q or "is pfz a guarantee" in q:
            return (
                "PFZ information is a scientific advisory, not a guarantee of fish availability. "
                "PFZs indicate areas where environmental conditions (such as favorable water temperature and chlorophyll) "
                "make fish more likely to gather. Actual fish presence depends on ocean currents, water depth, and local factors. "
                "Always check weather and sea conditions before heading out."
            )
        if any(k in q for k in ["where", "location", "find fish", "catch", "spots", "nearest"]):
            return (
                "Potential Fishing Zones (PFZ) are identified using satellite data on Sea Surface Temperature (SST) "
                "and chlorophyll concentrations. You can view current active PFZ coordinates on the NeerMitra navigation map. "
                "Before traveling to distant fishing zones, make sure to verify local wind and wave safety advisories."
            )
        return (
            "PFZ stands for Potential Fishing Zone. These are ocean areas where fish may be more abundant, "
            "identified using satellite data such as sea surface temperature (SST), chlorophyll concentration, and ocean fronts.\n\n"
            "PFZ information is a recommendation, not a guarantee of fish availability. "
            "Before going fishing, always consider weather conditions, wind and wave warnings, your boat's capacity, and local fishing knowledge."
        )

    # 3. SST / Sea Surface Temperature Questions
    if "sst" in q or "sea surface temperature" in q or "water temperature" in q:
        return (
            "SST stands for Sea Surface Temperature. It refers to the temperature of seawater at the ocean surface.\n\n"
            "Changes in SST create thermal fronts and nutrient upwelling zones where fish congregate, making SST an essential tool for identifying potential fishing zones."
        )

    # 4. IMBL / Maritime Boundary Questions
    if "imbl" in q or "international maritime boundary" in q or "border" in q or "boundary" in q or "sri lanka" in q:
        return (
            "IMBL stands for International Maritime Boundary Line. It is the official international maritime border separating the waters of neighboring nations (such as India and Sri Lanka).\n\n"
            "Fishermen must strictly avoid crossing the IMBL without authorization to prevent legal actions and ensure personal safety at sea."
        )

    # 5. Chlorophyll Questions
    if "chlorophyll" in q:
        return (
            "Chlorophyll-a is a green pigment found in microscopic marine plants called phytoplankton. "
            "High chlorophyll levels indicate rich biological productivity and abundant plankton, which attracts baitfish, tuna, mackerel, and sardines."
        )

    # 6. Wave Height / Wind Speed / Sea Conditions
    if any(k in q for k in ["wave", "waves", "swell", "sea condition", "rough sea"]):
        return (
            "Wave height measures the vertical distance between a wave's crest and trough. "
            "For small fishing craft, waves above 2.0 to 2.5 meters represent rough sea conditions. "
            "Always check wave forecasts and return to shore or harbor if high wave warnings are issued."
        )
    if any(k in q for k in ["wind", "winds", "breeze", "gale", "cyclone"]):
        return (
            "Wind speed affects ocean wave formation and boat stability. "
            "Winds exceeding 20-25 knots (around 40-50 km/h) create hazardous sea chop. "
            "Do not venture into sea during gale, squall, or cyclone advisories."
        )

    # 7. Safety check questions
    if "safe" in q or "safety" in q or intent == "SAFETY_CHECK":
        return (
            "Before going to sea, check the latest weather, wind speed, and wave height advisories. "
            "Ensure all crew members wear life jackets, and verify your boat's communication equipment (VHF/DAT), navigation lights, and emergency supplies."
        )

    # 8. EEZ
    if "eez" in q or "exclusive economic zone" in q:
        return (
            "EEZ stands for Exclusive Economic Zone. It extends up to 200 nautical miles from a coastal country's baseline, giving that country sovereign rights to explore, fish, and manage marine resources."
        )

    # 9. If facts exist, generate a clean summary
    if facts_str and len(facts_str) > 20:
        lines = [line.strip() for line in facts_str.split("\n") if line.strip() and not line.startswith("[") and not "Source:" in line and not "Chunk" in line]
        if lines:
            clean_fact_summary = " ".join(lines[:3])
            return f"{clean_fact_summary}\n\nSafe navigation and regular weather checks are advised for all fishing trips."

    return (
        "NeerMitra is ready to assist with marine conditions, potential fishing zones (PFZ), "
        "sea surface temperature (SST), weather forecasts, and safety advisories. How can I help you today?"
    )

def synthesize_marine_response(
    query: str,
    context_facts: Union[List[str], str] = "",
    language: str = "en",
    intent: str = "TERMINOLOGY_EXPLANATION"
) -> str:
    """
    Synthesize a clean, natural response for fishermen using Gemini LLM if configured,
    or our rich deterministic marine synthesizer.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    # Prepare clean context text
    if isinstance(context_facts, list):
        clean_context = "\n".join([clean_rag_leakage(f) for f in context_facts if f])
    else:
        clean_context = clean_rag_leakage(str(context_facts))

    if api_key:
        prompt = f"""Language: {language}
User Query: {query}
Detected Intent: {intent}
Relevant Marine Knowledge Context:
{clean_context}

Please provide a clean, helpful, conversational answer for the fisherman:"""

        # Try Google GenAI Client
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{NEERMITRA_SYSTEM_PROMPT}\n\n{prompt}"
            )
            if response and response.text:
                cleaned_text = clean_rag_leakage(response.text.strip())
                if cleaned_text:
                    return cleaned_text
        except Exception as e:
            logger.debug(f"google-genai call in synthesize_marine_response fallback: {e}")

        # Try legacy Google GenerativeAI
        try:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=api_key)
            model = genai_legacy.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(f"{NEERMITRA_SYSTEM_PROMPT}\n\n{prompt}")
            if response and response.text:
                cleaned_text = clean_rag_leakage(response.text.strip())
                if cleaned_text:
                    return cleaned_text
        except Exception as e:
            logger.debug(f"legacy google-genai call failed: {e}")

    # Fallback to rich deterministic synthesizer
    fallback = synthesize_deterministic_fallback(
        query=query,
        context_facts=clean_context,
        language=language,
        intent=intent
    )
    return clean_rag_leakage(fallback)

def ask_gemini(query: str) -> str:
    """
    Backward-compatible alias invoking synthesize_marine_response.
    """
    return synthesize_marine_response(query=query)
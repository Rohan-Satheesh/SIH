"""
nlp/llm/groq_client.py

Intelligent Marine Response Synthesis Engine for NeerMitra.
Provides contextual, fisherman-friendly response generation via Groq LLM
with a robust 3-tier fallback architecture: LLM -> RAG Fallback -> Deterministic Fallback.
"""

import os
import re
import logging
from typing import Optional, List, Union
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

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
6. Only provide real-time numerical data if it is explicitly present in the provided context. If asked for current data and it's not in the context, clearly state that current data is unavailable but explain the concept.
"""

# Deterministic Knowledge Base (Level 3 Fallback)
DETERMINISTIC_KNOWLEDGE = {
    "PFZ_LOCATION": "Potential Fishing Zones (PFZ) are oceanic areas where fish are likely to congregate. They are identified using satellite data on Sea Surface Temperature (SST) and chlorophyll. Before traveling to these zones, please verify local wind and wave safety advisories.",
    "TERMINOLOGY_EXPLANATION": "I am ready to help explain marine terms. For example, PFZ stands for Potential Fishing Zone, SST is Sea Surface Temperature, and IMBL is the International Maritime Boundary Line. Always check local weather and safety warnings before heading out.",
    "SST_QUERY": "SST stands for Sea Surface Temperature. It refers to the temperature of seawater at the ocean surface. Changes in SST create thermal fronts and nutrient upwelling zones where fish congregate.",
    "GEOFENCE_CHECK": "IMBL stands for International Maritime Boundary Line. It is the official international maritime border. Fishermen must strictly avoid crossing the IMBL without authorization to prevent legal actions and ensure personal safety.",
    "CHLOROPHYLL_QUERY": "Chlorophyll-a is a green pigment found in phytoplankton. High chlorophyll levels indicate rich biological productivity, which attracts baitfish, tuna, and mackerel.",
    "WEATHER_FORECAST": "Wind and waves strongly affect boat stability. Winds exceeding 20-25 knots create hazardous sea chop. Always check weather forecasts and avoid going to sea during gale or cyclone advisories.",
    "SAFETY_CHECK": "Safety First: Before going to sea, check the latest weather, wind speed, and wave height advisories. Ensure all crew members wear life jackets, and verify your boat's communication equipment.",
    "GENERAL_CONVERSATION": "Hello! I am NeerMitra, your marine and fishing assistant. I can help with ocean conditions, potential fishing zones (PFZ), sea surface temperature, weather safety, and maritime boundary navigation.",
    "UNSUPPORTED": "I am NeerMitra, a specialized marine and fishing assistant. I am best equipped to answer questions related to the sea, weather, fishing zones, or marine safety. Could you please ask a question related to these topics?"
}

def clean_rag_leakage(text: str) -> str:
    """
    Guardrail to ensure no raw document markers, chunk IDs, or internal file paths leak to user.
    """
    if not text:
        return ""
    
    cleaned = text
    cleaned = re.sub(r'\[Document\s+\d+\]\s*Source:.*?Chunk\s*ID:\s*\S+\s*Content:\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[Document\s+\d+\]\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Chunk\s*ID:\s*\S+\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Source:\s*\S+\.(txt|pdf|csv|json)\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bContent:\s*', '', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    return cleaned

def synthesize_rag_fallback(context_facts: str) -> Optional[str]:
    """
    Level 2 Fallback: If LLM fails but we have retrieved context, format it nicely.
    """
    if not context_facts or len(context_facts.strip()) < 20:
        return None
        
    lines = [line.strip() for line in context_facts.split("\n") if line.strip() and not line.startswith("[") and "Source:" not in line and "Chunk" not in line]
    if lines:
        clean_fact_summary = " ".join(lines[:3])
        return f"(Offline Mode) According to our knowledge base:\n\n{clean_fact_summary}\n\nSafe navigation and regular weather checks are advised for all fishing trips."
    return None

def synthesize_deterministic_fallback(
    query: str,
    intent: str = "TERMINOLOGY_EXPLANATION"
) -> str:
    """
    Level 3 Fallback: Deterministic natural language generator based on Intent Concepts.
    """
    if intent in DETERMINISTIC_KNOWLEDGE:
        return f"(Offline Mode) {DETERMINISTIC_KNOWLEDGE[intent]}"
        
    # If the intent isn't explicitly mapped, map to the default greeting
    return f"(Offline Mode) {DETERMINISTIC_KNOWLEDGE['GENERAL_CONVERSATION']}"

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def _call_groq_api(api_key: str, prompt: str, system_prompt: str = NEERMITRA_SYSTEM_PROMPT, response_format=None) -> Optional[str]:
    """Helper function to call Groq API with exponential backoff retries for 503s."""
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        kwargs = {
            "model": "qwen/qwen3.8-27b",
            "messages": messages,
            "temperature": 0.2,
            "max_completion_tokens": 512,
        }
        
        if response_format:
            kwargs["response_format"] = {"type": "json_object"}
            
        chat_completion = client.chat.completions.create(**kwargs)
        
        if chat_completion and chat_completion.choices:
            response_text = chat_completion.choices[0].message.content
            if response_text:
                if response_format:
                    return response_text.strip()
                cleaned_text = clean_rag_leakage(response_text.strip())
                if cleaned_text:
                    return cleaned_text
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        raise e
    return None

def synthesize_marine_response(
    query: str,
    context_facts: Union[List[str], str] = "",
    language: str = "en",
    intent: str = "TERMINOLOGY_EXPLANATION"
) -> str:
    """
    3-Tier Synthesis Strategy:
    1. Groq LLM (Primary)
    2. RAG Context summary (Secondary)
    3. Deterministic Concept Mapping (Tertiary)
    """
    api_key = os.getenv("GROQ_API_KEY")
    
    # Prepare clean context text
    if isinstance(context_facts, list):
        clean_context = "\n".join([clean_rag_leakage(f) for f in context_facts if f])
    else:
        clean_context = clean_rag_leakage(str(context_facts))

    # TIER 1: Groq LLM
    if api_key:
        prompt = f"Language: {language}\nUser Query: {query}\nDetected Intent: {intent}\nRelevant Marine Knowledge Context:\n{clean_context}\n\nPlease provide a clean, helpful, conversational answer for the fisherman:"
        try:
            res = _call_groq_api(api_key, prompt)
            if res:
                return res
        except Exception as e:
            logger.error(f"Groq API failure (falling back to offline modes): {e}")

    # TIER 2: RAG Context Summary
    if clean_context:
        rag_fallback = synthesize_rag_fallback(clean_context)
        if rag_fallback:
            return rag_fallback

    # TIER 3: Deterministic Fallback
    fallback = synthesize_deterministic_fallback(
        query=query,
        intent=intent
    )
    return fallback

def ask_gemini(query: str) -> str:
    """
    Backward-compatible alias invoking synthesize_marine_response.
    """
    return synthesize_marine_response(query=query)
import logging
from typing import Optional, Any
from nlp.llm.groq_client import _call_groq_api
import json

logger = logging.getLogger("neermitra.agents.explainer")

EXPLAINER_PROMPT = """You are NeerMitra, a highly intelligent marine and fishing assistant for coastal Indian fishermen.
You will be provided with raw data from various specialist agents (Weather, Ocean, Safety, Geo).
Your job is to synthesize this data into a clear, concise, conversational, and highly helpful response.

Guidelines:
1. Speak directly, respectfully, and clearly to the fisherman.
2. Translate complex data into practical advice. If weather is bad, explicitly warn them.
3. If they ask about Potential Fishing Zones (PFZ) or fish, use the Ocean Data (SST, chlorophyll) to explain conditions. Remind them that PFZ is a scientific advisory, not a guarantee of fish.
4. Always prioritize safety. If the Safety Agent says 'DANGER', start your response with a strong warning.
5. Do NOT output raw JSON or python objects in your response text. Write in natural language.
6. Only provide real-time numerical data if it is explicitly present in the provided context. If asked for current data and it's not in the context, clearly state that current data is unavailable.

Respond in the language the user is speaking, unless specified otherwise.
"""

def explainer_agent(
    query: str,
    weather_data: Optional[Any] = None,
    ocean_data: Optional[Any] = None,
    geo_data: Optional[Any] = None,
    safety_data: Optional[Any] = None,
    knowledge_data: Optional[Any] = None,
) -> dict:
    """
    Synthesizes reports from specialist agents using Groq LLM.
    """
    # Sanitize and truncate payload to prevent 413 Entity Too Large
    def _truncate(val, max_len=1500):
        s = str(val)
        return s[:max_len] + "..." if len(s) > max_len else s

    data_context = {
        "weather": _truncate(weather_data.model_dump() if hasattr(weather_data, "model_dump") else weather_data),
        "ocean": _truncate(ocean_data.model_dump() if hasattr(ocean_data, "model_dump") else ocean_data),
        "geo": _truncate(geo_data.model_dump() if hasattr(geo_data, "model_dump") else geo_data),
        "safety": _truncate(safety_data.model_dump() if hasattr(safety_data, "model_dump") else safety_data),
        "knowledge": _truncate(knowledge_data, max_len=2000) if knowledge_data else None,
    }
    
    prompt = f"User Query: {query}\n\nAgent Data Context:\n{json.dumps(data_context, indent=2)}\n\nPlease provide the final conversational response."
    
    api_key = __import__("os").getenv("GROQ_API_KEY")
    final_answer = ""
    
    if api_key:
        try:
            final_answer = _call_groq_api(
                api_key=api_key,
                prompt=prompt,
                system_prompt=EXPLAINER_PROMPT
            )
        except Exception as e:
            logger.error(f"Explainer LLM failed: {e}")
            
    if not final_answer:
        # Fallback if LLM fails
        safety_level = getattr(safety_data, "safety_level", "UNKNOWN") if safety_data else "UNKNOWN"
        if safety_level == "DANGER":
            final_answer = "(Offline Mode) DANGER: It is NOT safe to proceed. Hazardous conditions detected."
        elif safety_level == "CAUTION":
            final_answer = "(Offline Mode) Proceed with CAUTION. Sub-optimal conditions detected."
        else:
            final_answer = "(Offline Mode) Conditions appear generally SAFE based on available offline data."

    # Build metadata
    conditions = []
    sources = set()
    data_used = []
    
    def _get(obj, key):
        if obj is None:
            return None
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    wind = _get(weather_data, "wind_speed_knots")
    wave = _get(weather_data, "wave_height_m")
    w_sources = _get(weather_data, "source_timestamps") or {}
    
    if w_sources:
        sources.update(w_sources.keys())
    if wind is not None:
        data_used.append("wind_speed")
        conditions.append({"parameter": "wind_speed", "value": f"{wind} knots"})
    if wave is not None:
        data_used.append("wave_height")
        conditions.append({"parameter": "wave_height", "value": f"{wave} m"})
        
    sst = _get(ocean_data, "sst_celsius")
    o_sources = _get(ocean_data, "source_timestamps") or {}
    if o_sources:
        sources.update(o_sources.keys())
    if sst is not None:
        data_used.append("sst")
        conditions.append({"parameter": "sst", "value": f"{sst} °C"})
        
    valid_sources = [s for s in sources if s != "DATA_UNAVAILABLE"]
    
    return {
        "answer": final_answer,
        "intent": "unknown",
        "location": "Unknown",
        "date": "Today",
        "data_used": data_used,
        "conditions": conditions,
        "confidence": "high" if api_key else "low",
        "sources": valid_sources,
        "data_timestamp": "Now",
        "data_available": bool(data_used)
    }
import os
import logging
from typing import Optional, Any
from agents.prompts.system_prompt import ORCA_SYSTEM_PROMPT

logger = logging.getLogger("neermitra.agents.explainer")

def explainer_agent(
    query: str,
    weather_data: Optional[Any] = None,
    ocean_data: Optional[Any] = None,
    geo_data: Optional[Any] = None,
    safety_data: Optional[Any] = None,
) -> str:
    """
    Synthesizes reports from Weather, Ocean, Geospatial, and Safety agents
    into clear, actionable marine advisory for fishermen.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=api_key
            )
            prompt = f"""
USER QUERY: {query}
WEATHER: {weather_data}
OCEAN: {ocean_data}
GEOSPATIAL: {geo_data}
SAFETY: {safety_data}
"""
            response = llm.invoke([
                ("system", ORCA_SYSTEM_PROMPT),
                ("human", prompt),
            ])
            if isinstance(response.content, list):
                return "".join(
                    block.get("text", "")
                    for block in response.content
                    if isinstance(block, dict)
                )
            return str(response.content)
        except Exception as exc:
            logger.warning(f"LangChain explainer agent fallback: {exc}")

    # Deterministic Synthesis Fallback
    summary_parts = []
    if weather_data:
        w_risk = getattr(weather_data, 'risk_level', None) or (weather_data.get('risk_level') if isinstance(weather_data, dict) else 'SAFE')
        summary_parts.append(f"Weather conditions are evaluated as {w_risk}.")
    if geo_data:
        in_eez = getattr(geo_data, 'is_inside_eez', True) or (geo_data.get('is_inside_eez', True) if isinstance(geo_data, dict) else True)
        if in_eez:
            summary_parts.append("Vessel is within authorized Indian EEZ waters.")
        else:
            summary_parts.append("WARNING: Position indicates proximity to international boundary.")
    if safety_data:
        s_level = getattr(safety_data, 'overall_risk_level', None) or (safety_data.get('overall_risk_level') if isinstance(safety_data, dict) else 'LOW')
        summary_parts.append(f"Safety risk index: {s_level}.")

    if summary_parts:
        return " ".join(summary_parts) + " Safe navigation advised."
    return "Marine operational conditions are nominal. Continue monitoring live advisories."
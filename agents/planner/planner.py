"""
ORCA Planner Agent
[CHUNK_ID: R3-C02]

Uses Gemini to:
1. Understand the user's query.
2. Classify the user's intent.
3. Determine which specialist agents are required.
4. Decompose the request into subtasks.
"""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv

from agents.orchestrator.state import AgentState, PlannerOutput


# ============================================================
# Configuration
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

_llm = None

def get_planner_llm():
    global _llm
    if _llm is not None:
        return _llm
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            _llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=api_key,
                temperature=0,
            )
        except Exception:
            _llm = None
    return _llm


# ============================================================
# Planner Prompt
# ============================================================

PLANNER_SYSTEM_PROMPT = """
You are the ORCA Marine Intelligence Planner.

Your job is to analyze a user's marine-related request and create
a structured execution plan for specialist AI agents.

Available intents:

1. SAFETY_CHECK
   Questions about whether it is safe to travel, fish, sail,
   or operate a vessel.

2. PFZ_QUERY
   Questions about potential fishing zones, fish abundance,
   SST, chlorophyll, or ocean productivity.

3. WEATHER_QUERY
   Questions primarily about weather, wind, warnings, or waves.

4. ROUTE_PLANNING
   Questions about planning a marine route or choosing a safe route.

5. BOUNDARY_CHECK
   Questions about marine boundaries, restricted areas, EEZ,
   fishing zones, or geofences.

6. TREND_ANALYSIS
   Questions asking about historical or future trends.

Available specialist agents:

- weather
- ocean
- geospatial
- safety

Agent selection rules:

IMPORTANT:
Never include "safety" in required_agents.
Safety is always handled downstream by the LangGraph orchestrator
after the specialist agents complete.

SAFETY_CHECK:
    weather + ocean + geospatial

PFZ_QUERY:
    ocean + geospatial

WEATHER_QUERY:
    weather

ROUTE_PLANNING:
    weather + geospatial

BOUNDARY_CHECK:
    geospatial

TREND_ANALYSIS:
    ocean + weather

The planner must return ONLY valid JSON.

JSON structure:

{
    "intent": "SAFETY_CHECK",
    "required_agents": ["weather", "ocean", "geospatial", "safety"],
    "subtasks": [
        {
            "agent": "weather",
            "action": "get_weather",
            "params": {}
        }
    ]
}

Do not invent specialist agent names.

Keep the plan concise and directly related to the user request.
"""


# ============================================================
# JSON Parsing
# ============================================================


def _parse_json_response(content: Any) -> dict:
    """
    Convert Gemini's response into a Python dictionary.
    """

    if isinstance(content, list):
        content = "".join(
            part.get("text", "")
            if isinstance(part, dict)
            else str(part)
            for part in content
        )

    if not isinstance(content, str):
        content = str(content)

    content = content.strip()

    # Handle accidental Markdown code fences.
    if content.startswith("```"):
        lines = content.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

        if content.lower().startswith("json"):
            content = content[4:].strip()

    return json.loads(content)


# ============================================================
# Validation
# ============================================================


VALID_INTENTS = {
    "SAFETY_CHECK",
    "PFZ_QUERY",
    "WEATHER_QUERY",
    "ROUTE_PLANNING",
    "BOUNDARY_CHECK",
    "TREND_ANALYSIS",
}


VALID_AGENTS = {
    "weather",
    "ocean",
    "geospatial",
    "safety",
}


def _validate_plan(plan: dict) -> PlannerOutput:
    """
    Validate and normalize the Planner output.
    """

    intent = plan.get("intent")

    if intent not in VALID_INTENTS:
        raise ValueError(
            f"Invalid planner intent: {intent}"
        )

    required_agents = plan.get("required_agents", [])

    if not isinstance(required_agents, list):
        raise ValueError(
            "required_agents must be a list."
        )

    invalid_agents = set(required_agents) - VALID_AGENTS

    if invalid_agents:
        raise ValueError(
            f"Invalid planner agents: {invalid_agents}"
        )

    subtasks = plan.get("subtasks", [])

    if not isinstance(subtasks, list):
        raise ValueError(
            "subtasks must be a list."
        )

    return {
        "intent": intent,
        "required_agents": required_agents,
        "subtasks": subtasks,
    }


# ============================================================
# Planner
# ============================================================


def _heuristic_plan(query: str, location: list[float] | None = None) -> PlannerOutput:
    """Deterministic heuristic planning fallback when LLM is unavailable."""
    q = query.lower()
    
    if any(k in q for k in ["safe", "venture", "sail", "risk", "hazard", "warning", "surakshit", "safety", "can i go", "trip"]):
        intent = "SAFETY_CHECK"
        required = ["weather", "ocean", "geospatial"]
        subtasks = [
            {"agent": "weather", "action": "get_weather", "params": {}},
            {"agent": "ocean", "action": "get_ocean_conditions", "params": {}},
            {"agent": "geospatial", "action": "check_boundaries", "params": {}},
        ]
    elif any(k in q for k in ["fish", "pfz", "machhli", "meen", "chlorophyll", "catch", "potential", "hotspot", "shoal"]):
        intent = "PFZ_QUERY"
        required = ["ocean", "geospatial"]
        subtasks = [
            {"agent": "ocean", "action": "get_pfz_suitability", "params": {}},
            {"agent": "geospatial", "action": "get_nearest_pfz", "params": {}},
        ]
    elif any(k in q for k in ["wave", "wind", "weather", "tide", "swell", "cyclone", "storm", "barish", "hawa", "lehar", "forecast", "temp"]):
        intent = "WEATHER_QUERY"
        required = ["weather"]
        subtasks = [
            {"agent": "weather", "action": "get_weather", "params": {}},
        ]
    elif any(k in q for k in ["boundary", "border", "eez", "restricted", "sri lanka", "pakistan", "seema", "athirthi", "zone", "fence"]):
        intent = "BOUNDARY_CHECK"
        required = ["geospatial"]
        subtasks = [
            {"agent": "geospatial", "action": "check_boundaries", "params": {}},
        ]
    elif any(k in q for k in ["route", "waypoint", "path", "directions", "navigate", "bearing", "distance"]):
        intent = "ROUTE_PLANNING"
        required = ["weather", "geospatial"]
        subtasks = [
            {"agent": "weather", "action": "get_weather", "params": {}},
            {"agent": "geospatial", "action": "plan_safe_route", "params": {}},
        ]
    else:
        intent = "SAFETY_CHECK"
        required = ["weather", "ocean", "geospatial"]
        subtasks = [
            {"agent": "weather", "action": "get_weather", "params": {}},
            {"agent": "ocean", "action": "get_ocean_data", "params": {}},
            {"agent": "geospatial", "action": "analyze_location", "params": {}},
        ]

    return {
        "intent": intent,
        "required_agents": required,
        "subtasks": subtasks,
    }


def create_plan(state: AgentState) -> PlannerOutput:
    """
    Generate a plan from the user's current AgentState.
    """

    query = state.get("query", "")
    location = state.get("location")
    vessel_type = state.get("vessel_type")

    llm_instance = get_planner_llm()
    if llm_instance is not None:
        try:
            context = {
                "query": query,
                "location": location,
                "vessel_type": vessel_type,
            }

            prompt = (
                PLANNER_SYSTEM_PROMPT
                + "\n\nUSER REQUEST:\n"
                + json.dumps(context, default=str)
            )

            response = llm_instance.invoke(prompt)
            plan = _parse_json_response(response.content)
            return _validate_plan(plan)
        except Exception:
            pass

    return _heuristic_plan(query, location)


# ============================================================
# LangGraph Node
# ============================================================


def planner_node(state: AgentState) -> dict:
    """
    LangGraph-compatible Planner node.
    """

    try:
        plan = create_plan(state)

        return {
            "plan": plan,
            "active_agents": plan.get(
                "required_agents",
                [],
            ),
        }

    except Exception as exc:
        return {
            "error": f"Planner failed: {exc}"
        }
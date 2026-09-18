"""
ORCA Planner Agent
[CHUNK_ID: R3-C02]

Uses the LLM to understand the user's query and determine which
specialist agents are required.

A deterministic keyword fallback is also used for important marine
intents so that obvious PFZ, weather, safety, and geospatial queries
are not routed to the wrong specialist.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from agents.orchestrator.state import AgentState, PlannerOutput
from shared.schemas.query_schema import (
    QueryPlan,
    IntentType,
    AgentName,
    Subtask,
)

from nlp.llm.groq_client import _call_groq_api


logger = logging.getLogger("orca.planner")


PLANNER_PROMPT = """
You are the ORCA Agent Swarm Planner.

Analyze the user's query and output ONLY valid JSON.

Your job is to:

1. Identify the user's intent.
2. Identify the location if explicitly mentioned.
3. Select ONLY the specialist agents actually required.
4. Create useful subtasks.

Output JSON Schema:

{
  "intent": "SAFETY_CHECK" | "PFZ_QUERY" | "WEATHER_QUERY" |
            "ROUTE_PLANNING" | "BOUNDARY_CHECK" |
            "TREND_ANALYSIS" | "KNOWLEDGE_QUERY" | "UNKNOWN",

  "location": "Extract location name if explicitly present, else null",

  "required_agents": [
    "weather" | "ocean" | "geospatial" | "knowledge"
  ],

  "subtasks": [
    {
      "agent": "weather" | "ocean" | "geospatial" | "knowledge",
      "action": "Description of action",
      "params": {}
    }
  ]
}

Agent purposes:

- weather:
  Wind, waves, weather conditions, weather warnings, forecast.

- ocean:
  Sea surface temperature, chlorophyll, thermal fronts,
  Potential Fishing Zones (PFZ), ocean conditions.

- geospatial:
  Restricted areas, fishing bans, Marine Protected Areas,
  EEZ, IMBL, boundaries, geographic restrictions.

- knowledge:
  General explanations, guidelines, terminology, informational questions.

IMPORTANT INTENT RULES:

PFZ_QUERY:
Use this for:
- potential fishing zones
- potential fishing zone
- PFZ
- where are the fishing zones
- fishing zones
- fishing areas
- fishing locations
- where should I fish
- fishing zone information

For PFZ_QUERY, required_agents MUST include:
["ocean"]

Do NOT use weather as the primary agent for a PFZ_QUERY.

WEATHER_QUERY:
Use this for:
- weather
- wind
- waves
- forecast
- weather warnings
- weather conditions

For WEATHER_QUERY, required_agents should normally include:
["weather"]

SAFETY_CHECK:
Use this when the user explicitly asks:
- is it safe
- can I go fishing safely
- hazards
- danger
- safety
- risk

For SAFETY_CHECK, weather/ocean/geospatial may be required as supporting
agents.

BOUNDARY_CHECK:
Use this for:
- restricted area
- fishing ban
- marine protected area
- MPA
- EEZ
- boundary
- geographic restriction

For BOUNDARY_CHECK, required_agents should normally include:
["geospatial"]

Do not add unrelated agents.

Return only JSON.
"""


def _validate_plan(plan: QueryPlan) -> PlannerOutput:
    """
    Validate and normalize the Planner output.
    """

    intent = plan.intent.value

    # Safety is handled separately by the orchestrator.
    required_agents = [
        agent.value
        for agent in plan.required_agents
        if agent.value != "safety"
    ]

    subtasks = [
        {
            "agent": st.agent.value,
            "action": st.action,
            "params": st.params,
        }
        for st in plan.subtasks
    ]

    return {
        "intent": intent,
        "location": plan.location,
        "date": plan.date,
        "required_agents": required_agents,
        "subtasks": subtasks,
        "language": plan.language,
    }


# ============================================================
# Deterministic intent detection
# ============================================================


def _detect_query_intent(query: str) -> tuple[str | None, list[str]]:
    """
    Detect obvious marine intents deterministically.

    This is intentionally used as a safety net around the LLM planner.
    Obvious queries such as "Where are the potential fishing zones?"
    should never accidentally become weather queries.
    """

    q = str(query or "").strip().lower()

    if not q:
        return None, []

    # --------------------------------------------------------
    # PFZ / Fishing Zone
    # --------------------------------------------------------

    pfz_keywords = (
        "pfz",
        "potential fishing zone",
        "potential fishing zones",
        "fishing zone",
        "fishing zones",
        "fishing area",
        "fishing areas",
        "fishing location",
        "fishing locations",
        "where should i fish",
        "where can i fish",
    )

    if (
        any(keyword in q for keyword in pfz_keywords)
        and "restricted" not in q
    ):
        return "PFZ_QUERY", ["ocean"]

    # --------------------------------------------------------
    # Geospatial / Legal
    # --------------------------------------------------------

    geo_keywords = (
        "restricted area",
        "restricted areas",
        "restricted fishing area",
        "restricted fishing areas",
        "fishing ban",
        "fishing bans",
        "marine protected area",
        "marine protected areas",
        "mpa",
        "eez",
        "exclusive economic zone",
        "boundary",
        "boundaries",
        "geographic restriction",
        "geographical restriction",
    )

    if any(keyword in q for keyword in geo_keywords):
        return "BOUNDARY_CHECK", ["geospatial"]

    # --------------------------------------------------------
    # Safety
    # --------------------------------------------------------

    safety_keywords = (
        "is it safe",
        "safe to go fishing",
        "safely",
        "safety",
        "hazard",
        "hazards",
        "danger",
        "dangerous",
        "risk",
        "risks",
    )

    if any(keyword in q for keyword in safety_keywords):
        return "SAFETY_CHECK", [
            "weather",
            "ocean",
            "geospatial",
        ]

    # --------------------------------------------------------
    # Ocean
    # --------------------------------------------------------

    ocean_keywords = (
        "ocean",
        "sea temperature",
        "sea surface temperature",
        "sst",
        "chlorophyll",
        "thermal front",
        "thermal fronts",
    )

    if any(keyword in q for keyword in ocean_keywords):
        return "OCEAN_QUERY", ["ocean"]

    # --------------------------------------------------------
    # Weather
    # --------------------------------------------------------

    weather_keywords = (
        "weather",
        "wind",
        "winds",
        "wave",
        "waves",
        "forecast",
        "weather warning",
        "weather warnings",
    )

    if any(keyword in q for keyword in weather_keywords):
        return "WEATHER_QUERY", ["weather"]

    return None, []


def _build_plan_from_intent(
    query: str,
    intent: str,
    required_agents: list[str],
    location: Any = None,
    language: str = "en",
) -> PlannerOutput:
    """
    Build a deterministic PlannerOutput.
    """

    subtasks = []

    for agent in required_agents:
        if agent == "ocean":
            action = "Fetch ocean conditions and PFZ information."

        elif agent == "weather":
            action = "Fetch current weather conditions and warnings."

        elif agent == "geospatial":
            action = "Check geographic boundaries and restrictions."

        elif agent == "knowledge":
            action = "Retrieve relevant knowledge and guidelines."

        else:
            action = "Process the query using the specialist agent."

        subtasks.append(
            {
                "agent": agent,
                "action": action,
                "params": {},
            }
        )

    return {
        "intent": intent,
        "location": location,
        "date": "Today",
        "required_agents": required_agents,
        "subtasks": subtasks,
        "language": language,
    }


# ============================================================
# LLM Planner
# ============================================================


def create_plan(state: AgentState) -> PlannerOutput:
    """
    Generate a plan from the user's current AgentState.

    The LLM is used first, but obvious marine intents are normalized
    deterministically afterwards.
    """

    query = state.get("query", "")
    location = state.get("location")
    language = state.get("language", "en")

    # --------------------------------------------------------
    # Deterministic classification
    # --------------------------------------------------------

    detected_intent, detected_agents = _detect_query_intent(query)

    logger.debug(
        "Deterministic intent detection: query=%r intent=%s agents=%s",
        query,
        detected_intent,
        detected_agents,
    )

    # --------------------------------------------------------
    # LLM planner
    # --------------------------------------------------------

    api_key = os.getenv("GROQ_API_KEY")

    if api_key:
        try:
            res_text = _call_groq_api(
                api_key=api_key,
                prompt=f"User Query: {query}",
                system_prompt=PLANNER_PROMPT,
                response_format="json_object",
            )

            if res_text:
                plan_dict = json.loads(res_text)

                intent_val = plan_dict.get(
                    "intent",
                    "UNKNOWN",
                )

                try:
                    intent_enum = IntentType(intent_val)
                except Exception:
                    intent_enum = IntentType.UNKNOWN

                # ------------------------------------------------
                # Parse required agents
                # ------------------------------------------------

                req_agents = []

                for ra in plan_dict.get(
                    "required_agents",
                    [],
                ):
                    try:
                        req_agents.append(
                            AgentName(ra)
                        )
                    except Exception:
                        logger.debug(
                            "Ignoring unknown agent from planner: %s",
                            ra,
                        )

                # ------------------------------------------------
                # Parse subtasks
                # ------------------------------------------------

                subtasks = []

                for st in plan_dict.get(
                    "subtasks",
                    [],
                ):
                    try:
                        subtasks.append(
                            Subtask(
                                agent=AgentName(st["agent"]),
                                action=st["action"],
                                params=st.get(
                                    "params",
                                    {},
                                ),
                            )
                        )
                    except Exception:
                        continue

                # ------------------------------------------------
                # IMPORTANT:
                #
                # Deterministic classification overrides the LLM
                # for obvious queries.
                # ------------------------------------------------

                if detected_intent is not None:
                    logger.info(
                        "Overriding LLM planner intent %s -> %s for query=%r",
                        intent_enum.value,
                        detected_intent,
                        query,
                    )

                    return _build_plan_from_intent(
                        query=query,
                        intent=detected_intent,
                        required_agents=detected_agents,
                        location=plan_dict.get(
                            "location"
                        ),
                        language=language,
                    )

                # ------------------------------------------------
                # Normal LLM plan
                # ------------------------------------------------

                plan_obj = QueryPlan(
                    intent=intent_enum,
                    location=plan_dict.get(
                        "location"
                    ),
                    date="Today",
                    language=language,
                    required_agents=req_agents,
                    subtasks=subtasks,
                )

                return _validate_plan(plan_obj)

        except Exception as exc:
            logger.exception(
                "Planner LLM failed: %s",
                exc,
            )

    # --------------------------------------------------------
    # Deterministic fallback
    # --------------------------------------------------------

    if detected_intent is not None:
        logger.info(
            "Using deterministic planner fallback: intent=%s agents=%s",
            detected_intent,
            detected_agents,
        )

        return _build_plan_from_intent(
            query=query,
            intent=detected_intent,
            required_agents=detected_agents,
            location=location,
            language=language,
        )

    # --------------------------------------------------------
    # Final fallback
    # --------------------------------------------------------

    return _build_plan_from_intent(
        query=query,
        intent="SAFETY_CHECK",
        required_agents=[
            "weather",
            "ocean",
            "geospatial",
        ],
        location=location,
        language=language,
    )


# ============================================================
# LangGraph Node
# ============================================================


def planner_node(state: AgentState) -> dict:
    """
    LangGraph-compatible Planner node.
    """

    try:
        plan = create_plan(state)

        logger.info(
            "Planner result: intent=%s required_agents=%s",
            plan.get("intent"),
            plan.get("required_agents"),
        )

        return {
            "plan": plan,
            "active_agents": plan.get(
                "required_agents",
                [],
            ),
        }

    except Exception as exc:
        logger.exception(
            "Planner node failed: %s",
            exc,
        )

        return {
            "error": [f"Planner failed: {exc}"]
        }
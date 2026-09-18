"""
ORCA Agent Orchestrator — Conditional Routing Logic
[CHUNK_ID: R3-C01]

Routing functions that determine which specialist agents to invoke
based on the Planner's task decomposition output.

PRD Reference: §9.7.3 R3-C01
Master System Prompt: §3
"""

from __future__ import annotations

from typing import Literal, Sequence

from agents.orchestrator.state import AgentState


# ─────────────────────────────────────────────────────────────
# Fan-Out Router — After Planner
# ─────────────────────────────────────────────────────────────
# LangGraph uses Send() for parallel fan-out. This function
# returns the list of agent node names the planner selected.
# ─────────────────────────────────────────────────────────────

# All possible specialist agent node names
SPECIALIST_AGENTS = {"weather_agent", "ocean_agent", "geospatial_agent", "knowledge_agent"}

# Mapping from plan agent keys → graph node names
AGENT_KEY_TO_NODE = {
    "weather": "weather_agent",
    "ocean": "ocean_agent",
    "geospatial": "geospatial_agent",
    "knowledge": "knowledge_agent",
}

# Default agents when no plan is available
DEFAULT_AGENTS = ["weather_agent", "ocean_agent", "geospatial_agent"]


def route_after_planner(state: AgentState) -> list[str]:
    plan = state.get("plan") or {}
    required = plan.get("required_agents") or []

    if not required:
        return DEFAULT_AGENTS

    routes = []

    for agent in required:
        node = AGENT_KEY_TO_NODE.get(agent)

        if node and node in SPECIALIST_AGENTS:
            routes.append(node)

    return routes or DEFAULT_AGENTS


def should_run_safety(state: AgentState) -> str:
    plan = state.get("plan") or {}

    intent = str(plan.get("intent") or "").upper()
    required = plan.get("required_agents") or []

    if intent == "SAFETY_CHECK":
        return "safety_agent"

    if "safety" in required:
        return "safety_agent"

    informational_intents = {
        "PFZ_QUERY",
        "OCEAN_QUERY",
        "WEATHER_QUERY",
        "BOUNDARY_CHECK",
        "TREND_ANALYSIS",
        "GENERAL_INFO",
        "KNOWLEDGE_QUERY",
    }

    if intent in informational_intents:
        return "explainer"

    return "safety_agent"



def check_for_errors(state: AgentState) -> Literal["explainer", "error_handler"]:
    """
    Check if any critical errors occurred during specialist execution.
    If so, route to error handler instead of explainer.
    """
    error = state.get("error")
    if error:
        return "error_handler"
    return "explainer"

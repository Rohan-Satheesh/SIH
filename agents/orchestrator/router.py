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
SPECIALIST_AGENTS = {"weather_agent", "ocean_agent", "geospatial_agent"}

# Mapping from plan agent keys → graph node names
AGENT_KEY_TO_NODE = {
    "weather": "weather_agent",
    "ocean": "ocean_agent",
    "geospatial": "geospatial_agent",
}

# Default agents when no plan is available
DEFAULT_AGENTS = ["weather_agent", "ocean_agent", "geospatial_agent"]


def route_after_planner(state: AgentState) -> list[str]:
    """
    Conditional edge function called after the Planner node.

    Reads `state["plan"]["required_agents"]` and returns the list
    of specialist node names to fan out to.

    If plan is missing or empty, defaults to running ALL specialist agents
    (fail-safe: always gather some data).

    Returns:
        List of node name strings for LangGraph to route to.
    """
    plan = state.get("plan")

    if not plan or not plan.get("required_agents"):
        # No plan or empty agent list — run all specialists
        return DEFAULT_AGENTS

    required = plan["required_agents"]
    nodes = []

    for agent_key in required:
        node_name = AGENT_KEY_TO_NODE.get(agent_key)
        if node_name:
            nodes.append(node_name)

    # Always include at least one agent
    if not nodes:
        return DEFAULT_AGENTS

    return nodes


def should_run_safety(state: AgentState) -> Literal["safety_agent", "explainer"]:
    """
    After specialist agents complete, determine whether to run the
    Safety Agent or skip directly to the Explainer.

    Safety agent runs if:
    - The plan explicitly includes "safety" in required_agents, OR
    - Weather data indicates potential hazards, OR
    - We always run it (default safe behavior)

    In practice, we almost always run safety — it's the core value prop.
    """
    plan = state.get("plan")

    # Check if safety was explicitly excluded
    if plan and plan.get("required_agents"):
        required = plan["required_agents"]
        # Only skip safety for pure informational queries
        if "safety" not in required and plan.get("intent") in ("TREND_ANALYSIS", "GENERAL_INFO"):
            return "explainer"

    # Default: always run safety agent
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

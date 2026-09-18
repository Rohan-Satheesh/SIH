"""
ORCA Agent Orchestrator — Shared Agent State
[CHUNK_ID: R3-C01]

Defines the TypedDict that flows through the entire LangGraph state machine.
Every agent node reads from and writes to this shared state.

PRD Reference: §9.7.3 R3-C01
Master System Prompt: §3, §4.1
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Optional, TypedDict

from shared.schemas.chat_schema import EvidenceTrail, MapAction, DashboardMetrics
from shared.schemas.marine_schema import WeatherReport, OceanReport, SafetyAssessment
from shared.schemas.geo_schema import BoundaryCheck, PFZResult


# ─────────────────────────────────────────────────────────────
# Planner Output — Task Decomposition Plan
# ─────────────────────────────────────────────────────────────
class SubTask(TypedDict, total=False):
    """A single sub-task assigned by the Planner to a specialist agent."""
    agent: str                      # "weather", "ocean", "safety", "geospatial"
    action: str                     # Tool/function to invoke
    params: dict                    # Parameters for the tool call


class PlannerOutput(TypedDict, total=False):
    """Structured output from the Planner Agent."""
    intent: str                     # Intent category (e.g., "SAFETY_CHECK", "PFZ_QUERY")
    user_location: list[float]      # [lat, lon] — resolved from input or GPS
    target_time_window: str         # "now", "tomorrow_morning", "7day"
    vessel_type: str                # "small_craft_7m", "motorized_10m", "deep_sea_trawler_15m"
    required_agents: list[str]      # ["weather", "ocean", "safety", "geospatial"]
    subtasks: list[SubTask]         # Ordered sub-task list


# ─────────────────────────────────────────────────────────────
# Agent State — Core LangGraph State Schema
# ─────────────────────────────────────────────────────────────
class AgentState(TypedDict, total=False):
    """
    The shared state object passed between all nodes in the
    ORCA LangGraph state machine.

    ┌──────────────────┐
    │  INPUT FIELDS    │  Set at graph invocation
    ├──────────────────┤
    │  PLANNER OUTPUT  │  Set by Planner Agent
    ├──────────────────┤
    │  SPECIALIST DATA │  Set by Weather/Ocean/Geo agents
    ├──────────────────┤
    │  SAFETY OUTPUT   │  Set by Safety & Risk Agent
    ├──────────────────┤
    │  SYNTHESIS       │  Set by Explainer Agent
    ├──────────────────┤
    │  CONTROL         │  Routing and error handling
    └──────────────────┘
    """

    # ── Input Fields (set at graph invocation) ──
    query: str                                  # User's natural language query
    language: str                               # ISO language code (e.g., "en", "ml", "ta")
    session_id: str                             # Session identifier for multi-turn context
    location: Optional[list[float]]             # User GPS [lat, lon]
    vessel_type: Optional[str]                  # Vessel specification key
    chat_history: Optional[list[dict]]          # Previous messages for context

    # ── Planner Output ──
    plan: Optional[PlannerOutput]               # Task decomposition from Planner Agent

    # ── Specialist Agent Outputs ──
    weather_data: Optional[WeatherReport]       # From Weather Agent
    ocean_data: Optional[OceanReport]           # From Ocean Agent
    geo_data: Optional[BoundaryCheck]           # From Geospatial Agent
    pfz_data: Optional[list[PFZResult]]         # PFZ nearest-neighbor results
    knowledge_data: Optional[dict]              # From Knowledge Agent

    # ── Safety & Risk Output ──
    safety_data: Optional[SafetyAssessment]     # From Safety & Risk Agent

    # ── Synthesis / Final Output ──
    final_response: Optional[str]               # Markdown response text
    map_actions: Annotated[list[MapAction], operator.add]  # Accumulated map commands
    dashboard_metrics: Optional[DashboardMetrics]
    evidence_trail: Optional[EvidenceTrail]     # Data provenance block

    # ── Control Flow ──
    error: Annotated[list[str], operator.add]   # Accumulated error messages                    # Error message if any agent fails
    active_agents: Optional[list[str]]          # Which specialist agents are running
    completed_agents: Annotated[list[str], operator.add]  # Track completed agents

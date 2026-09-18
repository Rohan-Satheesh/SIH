"""
ORCA Agent Orchestrator — LangGraph State Machine
[CHUNK_ID: R3-C01]

Flow:

    START
      ↓
    Planner
      ↓
    Specialist Agents (parallel)
      ├── Weather
      ├── Ocean
      └── Geospatial
      ↓
    Specialist Join
      ↓
    Safety
      ↓
    Explainer
      ↓
    END

Currently uses mock agent nodes.
Real implementations will replace the mocks in R3-C02 through R3-C07.
"""

from __future__ import annotations

try:
    from langgraph.graph import StateGraph, START, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    START = "__start__"
    END = "__end__"

    class StateGraph:
        def __init__(self, state_schema):
            self.state_schema = state_schema
            self.nodes = {}
            self.edges = []
            self.conditional_edges = []

        def add_node(self, name, func):
            self.nodes[name] = func

        def add_edge(self, from_node, to_node):
            self.edges.append((from_node, to_node))

        def add_conditional_edges(self, source, router_fn, path_map):
            self.conditional_edges.append((source, router_fn, path_map))

        def compile(self, checkpointer=None):
            return CompiledGraph(self)

    class CompiledGraph:
        def __init__(self, graph):
            self.graph = graph

        def invoke(self, state, config=None):
            curr_state = dict(state)

            # 1. Planner
            if "planner" in self.graph.nodes:
                res = self.graph.nodes["planner"](curr_state)
                if isinstance(res, dict):
                    curr_state.update(res)

            # 2. Specialist fan-out
            plan = curr_state.get("plan", {})
            req_agents = plan.get(
                "required_agents",
                ["weather", "ocean", "geospatial"],
            )

            for agent_name in req_agents:
                node_key = (
                    f"{agent_name}_agent"
                    if not agent_name.endswith("_agent")
                    else agent_name
                )

                if node_key in self.graph.nodes:
                    res = self.graph.nodes[node_key](curr_state)

                    if isinstance(res, dict):
                        for k, v in res.items():
                            if (
                                k == "completed_agents"
                                and "completed_agents" in curr_state
                            ):
                                curr_state["completed_agents"] = list(
                                    set(
                                        curr_state["completed_agents"] + v
                                    )
                                )

                            elif k == "error" and "error" in curr_state:
                                curr_state["error"] = (
                                    curr_state["error"] + v
                                )

                            else:
                                curr_state[k] = v

            # 3. Specialist Join
            if "specialist_join" in self.graph.nodes:
                self.graph.nodes["specialist_join"](curr_state)

            # 4. Safety Agent
            safety_route = should_run_safety(curr_state)

            if (
                safety_route == "safety_agent"
                and "safety_agent" in self.graph.nodes
            ):
                res = self.graph.nodes["safety_agent"](curr_state)

                if isinstance(res, dict):
                    for k, v in res.items():
                        if (
                            k == "completed_agents"
                            and "completed_agents" in curr_state
                        ):
                            curr_state["completed_agents"] = list(
                                set(
                                    curr_state["completed_agents"] + v
                                )
                            )

                        elif k == "error" and "error" in curr_state:
                            curr_state["error"] = (
                                curr_state["error"] + v
                            )

                        else:
                            curr_state[k] = v

            # 5. Explainer
            if "explainer" in self.graph.nodes:
                res = self.graph.nodes["explainer"](curr_state)

                if isinstance(res, dict):
                    for k, v in res.items():
                        if (
                            k == "completed_agents"
                            and "completed_agents" in curr_state
                        ):
                            curr_state["completed_agents"] = list(
                                set(
                                    curr_state["completed_agents"] + v
                                )
                            )

                        elif k == "error" and "error" in curr_state:
                            curr_state["error"] = (
                                curr_state["error"] + v
                            )

                        else:
                            curr_state[k] = v

            return curr_state


from agents.agents.explainer_agent import (
    explainer_agent as run_explainer_agent
)
from agents.agents.geospatial_agent import (
    geospatial_agent as run_geospatial_agent
)
from agents.agents.safety_agent import (
    safety_agent as run_safety_agent
)
from agents.agents.weather_agent import (
    weather_agent as run_weather_agent
)
from agents.agents.ocean_agent import (
    ocean_agent as run_ocean_agent
)
from agents.agents.knowledge_agent import (
    knowledge_agent as run_knowledge_agent
)

from agents.orchestrator.checkpointer import checkpointer
from agents.orchestrator.state import AgentState

from agents.orchestrator.router import (
    route_after_planner,
    should_run_safety,
)

from agents.planner.planner import planner_node


# ============================================================
# Planner Mock
# ============================================================


# ============================================================
# Specialist Agent Mocks
# ============================================================


def weather_agent_node(state: AgentState):
    """
    LangGraph node for the real ORCA Weather Agent.
    """

    location = state.get("location")

    if not location or len(location) != 2:
        return {
            "error": [
                "Weather Agent requires [latitude, longitude]."
            ]
        }

    latitude = location[0]
    longitude = location[1]

    try:
        report = run_weather_agent(
            latitude=latitude,
            longitude=longitude,
        )

        return {
            "weather_data": report,
            "completed_agents": ["weather_agent"],
        }

    except Exception as exc:
        return {
            "error": [f"Weather Agent failed: {exc}"],
            "completed_agents": ["weather_agent"],
        }


def ocean_agent_node(state: AgentState) -> dict:
    location = state.get("location")

    if not location or len(location) != 2:
        return {
            "error": [
                "Ocean Agent requires [latitude, longitude]."
            ],
            "completed_agents": ["ocean_agent"],
        }

    latitude = location[0]
    longitude = location[1]

    try:
        report = run_ocean_agent(
            latitude=latitude,
            longitude=longitude,
        )

        return {
            "ocean_data": report,
            "completed_agents": ["ocean_agent"],
        }

    except Exception as exc:
        return {
            "error": [f"Ocean Agent failed: {exc}"],
            "completed_agents": ["ocean_agent"],
        }


def geospatial_agent_node(state: AgentState) -> dict:
    location = state.get("location")

    if not location or len(location) != 2:
        return {
            "error": [
                "Geospatial Agent requires [latitude, longitude]."
            ],
            "completed_agents": ["geospatial_agent"],
        }

    try:
        report = run_geospatial_agent(
            latitude=location[0],
            longitude=location[1],
        )

        return {
            "geo_data": report,
            "completed_agents": ["geospatial_agent"],
        }

    except Exception as exc:
        return {
            "error": [f"Geospatial Agent failed: {exc}"],
            "completed_agents": ["geospatial_agent"],
        }


def knowledge_agent_node(state: AgentState) -> dict:
    query = state.get("query", "")

    try:
        report = run_knowledge_agent(query)

        return {
            "knowledge_data": report,
            "completed_agents": ["knowledge_agent"],
        }

    except Exception as exc:
        return {
            "error": [f"Knowledge Agent failed: {exc}"],
            "completed_agents": ["knowledge_agent"],
        }


# ============================================================
# Synchronization / Join Node
# ============================================================


def specialist_join_node(state: AgentState) -> dict:
    """
    Synchronization point for specialist agents.

    LangGraph reaches this node only after all specialist
    branches that were routed from the Planner have completed.

    No manual completion checking is required here.
    """

    return {}


# ============================================================
# Safety Agent Mock
# ============================================================


def safety_agent_node(state: AgentState) -> dict:
    weather_data = state.get("weather_data")
    ocean_data = state.get("ocean_data")
    geo_data = state.get("geo_data")
    vessel_type = state.get("vessel_type")

    try:
        report = run_safety_agent(
            weather_data=weather_data,
            ocean_data=ocean_data,
            geo_data=geo_data,
            vessel_type=vessel_type,
        )

        return {
            "safety_data": report,
            "completed_agents": ["safety_agent"],
        }

    except Exception as exc:
        return {
            "error": [f"Safety Agent failed: {exc}"],
            "completed_agents": ["safety_agent"],
        }


# ============================================================
# Explainer Agent Mock
# ============================================================


def explainer_node(state: AgentState) -> dict:
    """
    LangGraph node for the real ORCA Explainer Agent.
    """

    try:
        # Get the structured Planner output so the Explainer
        # knows what kind of question the user actually asked.
        plan = state.get("plan") or {}

        response = run_explainer_agent(
            query=state.get("query", ""),
            weather_data=state.get("weather_data"),
            ocean_data=state.get("ocean_data"),
            geo_data=state.get("geo_data"),
            safety_data=state.get("safety_data"),
            knowledge_data=state.get("knowledge_data"),

            # Planner context
            intent=plan.get("intent"),
            location=plan.get("location"),
            date=plan.get("date"),
        )

        return {
            "final_response": response,
            "completed_agents": ["explainer"],
        }

    except Exception as exc:
        return {
            "error": [f"Explainer Agent failed: {exc}"],
            "completed_agents": ["explainer"],
        }


# ============================================================
# Error Handler Mock
# ============================================================


def error_handler_node(state: AgentState) -> dict:
    """
    Temporary error handler.
    """

    return {
        "final_response": (
            "ORCA could not complete the requested analysis."
        )
    }


# ============================================================
# Build Graph
# ============================================================


def build_graph():
    """
    Construct and compile the ORCA LangGraph.

    Returns:
        Compiled LangGraph application.
    """

    graph = StateGraph(AgentState)

    # --------------------------------------------------------
    # Register Nodes
    # --------------------------------------------------------

    graph.add_node("planner", planner_node)

    graph.add_node(
        "weather_agent",
        weather_agent_node,
    )

    graph.add_node(
        "ocean_agent",
        ocean_agent_node,
    )

    graph.add_node(
        "geospatial_agent",
        geospatial_agent_node,
    )

    graph.add_node(
        "knowledge_agent",
        knowledge_agent_node,
    )

    graph.add_node(
        "specialist_join",
        specialist_join_node,
    )

    graph.add_node(
        "safety_agent",
        safety_agent_node,
    )

    graph.add_node(
        "explainer",
        explainer_node,
    )

    graph.add_node(
        "error_handler",
        error_handler_node,
    )

    # --------------------------------------------------------
    # START → Planner
    # --------------------------------------------------------

    graph.add_edge(
        START,
        "planner",
    )

    # --------------------------------------------------------
    # Planner → Specialist Fan-Out
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "weather_agent": "weather_agent",
            "ocean_agent": "ocean_agent",
            "geospatial_agent": "geospatial_agent",
            "knowledge_agent": "knowledge_agent",
        },
    )

    # --------------------------------------------------------
    # Specialists → Join
    # --------------------------------------------------------

    graph.add_edge(
        "weather_agent",
        "specialist_join",
    )

    graph.add_edge(
        "ocean_agent",
        "specialist_join",
    )

    graph.add_edge(
        "geospatial_agent",
        "specialist_join",
    )

    graph.add_edge(
        "knowledge_agent",
        "specialist_join",
    )

    # --------------------------------------------------------
    # Join → Safety / Explainer
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "specialist_join",
        should_run_safety,
        {
            "safety_agent": "safety_agent",
            "explainer": "explainer",
        },
    )

    # --------------------------------------------------------
    # Safety → Explainer
    # --------------------------------------------------------

    graph.add_edge(
        "safety_agent",
        "explainer",
    )

    # --------------------------------------------------------
    # Explainer → END
    # --------------------------------------------------------

    graph.add_edge(
        "explainer",
        END,
    )

    # --------------------------------------------------------
    # Error Handler → END
    # --------------------------------------------------------

    graph.add_edge(
        "error_handler",
        END,
    )

    return graph.compile(checkpointer=checkpointer)


# ============================================================
# Compiled ORCA Graph
# ============================================================


orca_graph = build_graph()


# ============================================================
# Chat Controller Bridge Function
# ============================================================

import logging

from agents.memory.context_store import extract_target_location

logger = logging.getLogger("orca.orchestrator")


def run_marine_agent(
    engine: Any = None,
    query: str = "",
    language: str = "EN",
    context: Optional[dict] = None,
    session_id: Optional[str] = "default",
    history: Optional[list] = None,
) -> dict:
    """
    Bridge function executing the LangGraph multi-agent swarm.
    Extracts user location, runs specialist agents, and constructs
    CopilotResponse dict.
    """

    lat, lon, loc_name = extract_target_location(
        query,
        session=None,
        context=context,
    )

    vessel = "motorized_10m"

    if (
        context
        and isinstance(context, dict)
        and context.get("vessel_type")
    ):
        vessel = context.get("vessel_type")

    initial_state: AgentState = {
        "query": query,
        "language": language or "en",
        "session_id": session_id or "default",
        "location": [lat, lon],
        "vessel_type": vessel,
        "chat_history": history or [],
        "completed_agents": [],
        "error": [],
    }

    try:
        config = {
            "configurable": {
                "thread_id": session_id or "default"
            }
        }

        final_state = orca_graph.invoke(
            initial_state,
            config=config,
        )

    except Exception as exc:
        logger.error(
            f"LangGraph execution failed: {exc}"
        )

        final_state = dict(initial_state)

        final_state["final_response"] = {
            "answer": (
                "I apologize, but I am currently unable "
                "to process your request due to an internal "
                "system error."
            ),
            "intent": "UNKNOWN",
            "conditions": [],
            "confidence": "low",
            "sources": [],
            "data_available": False,
        }

    explainer_output = (
        final_state.get("final_response") or {}
    )

    final_text = ""
    confidence = 95
    sources = []

    if isinstance(explainer_output, str):
        final_text = explainer_output

    elif isinstance(explainer_output, dict):
        final_text = explainer_output.get(
            "answer",
            "",
        )

        conf_str = str(
            explainer_output.get(
                "confidence",
                "high",
            )
        ).lower()

        confidence = (
            95
            if conf_str == "high"
            else (
                70
                if conf_str == "medium"
                else 40
            )
        )

        sources = explainer_output.get(
            "sources",
            [],
        )

    weather_data = final_state.get(
        "weather_data"
    )

    ocean_data = final_state.get(
        "ocean_data"
    )

    safety_data = final_state.get(
        "safety_data"
    )

    geo_data = final_state.get(
        "geo_data"
    )

    completed = (
        final_state.get("completed_agents")
        or []
    )

    # Run friend's NLP translation on the final response!
    try:
        from nlp.translation.translator import (
            translate_response
        )

        lang_code = (
            language.lower()
            if language
            else "en"
        )

        final_text = translate_response(
            final_text,
            lang_code,
        )

    except Exception as e:
        logger.error(
            f"NLP Translation failed: {e}"
        )

    # Build telemetry conditions
    conditions: list[str] = []

    if (
        isinstance(explainer_output, dict)
        and explainer_output.get("conditions")
    ):
        for c in explainer_output.get(
            "conditions",
            [],
        ):
            conditions.append(
                f"{c.get('parameter', '')}: "
                f"{c.get('value', '')} "
                f"({c.get('interpretation', '')})"
            )

    else:
        if weather_data:
            if (
                weather_data.wave_height_m
                is not None
            ):
                conditions.append(
                    f"Wave Height: "
                    f"{weather_data.wave_height_m:.1f} m"
                )

            if (
                weather_data.wind_speed_knots
                is not None
            ):
                dir_str = (
                    f" ({weather_data.wind_direction}°)"
                    if weather_data.wind_direction
                    else ""
                )

                conditions.append(
                    f"Wind Speed: "
                    f"{weather_data.wind_speed_knots:.1f} "
                    f"kts{dir_str}"
                )

            if weather_data.imd_warning_active:
                conditions.append(
                    "IMD Advisory: ACTIVE"
                )

        if ocean_data:
            if (
                ocean_data.sst_celsius
                is not None
            ):
                conditions.append(
                    f"SST: "
                    f"{ocean_data.sst_celsius:.1f} °C"
                )

            if (
                ocean_data.chlorophyll_mg_m3
                is not None
            ):
                conditions.append(
                    f"Chlorophyll: "
                    f"{ocean_data.chlorophyll_mg_m3:.2f} "
                    f"mg/m³"
                )

            if (
                ocean_data.pfz_suitability_score
                is not None
            ):
                if ocean_data.pfz_suitability_score is not None:
                    pfz_score = ocean_data.pfz_suitability_score * 100

                    pfz_text = f"PFZ Suitability: {pfz_score:.0f}/100"

                    if ocean_data.pfz_classification:
                        pfz_text += f" ({ocean_data.pfz_classification})"

                    conditions.append(pfz_text)

    # Determine risk level
    #
    # Only Safety/Weather queries should drive the global risk badge.
    # Geospatial/PFZ/informational queries should not inherit a
    # safety-agent risk value merely because the agent was invoked.

    plan_intent = str(
        (final_state.get("plan") or {}).get("intent") or ""
    ).upper()

    risk_level = "LOW"

    if plan_intent in {
        "SAFETY_CHECK",
        "WEATHER_QUERY",
    }:
        if safety_data:
            lvl = (
                getattr(safety_data, "safety_level", None)
                or getattr(safety_data, "safety_decision", None)
                or ""
            )

            lvl_str = str(lvl).upper()

            if (
                "DANGER" in lvl_str
                or "NO-GO" in lvl_str
                or "HIGH" in lvl_str
            ):
                risk_level = "HIGH"

            elif (
                "CAUTION" in lvl_str
                or "MODERATE" in lvl_str
                or (
                    hasattr(safety_data, "composite_risk_score")
                    and safety_data.composite_risk_score is not None
                    and safety_data.composite_risk_score >= 0.36
                )
            ):
                risk_level = "MODERATE"

        elif (
            weather_data
            and getattr(weather_data, "weather_risk_level", None)
            == "DANGER"
        ):
            risk_level = "HIGH"

    spatial_payload = {
        "location_name": loc_name,
        "coordinates": {
            "lat": lat,
            "lon": lon,
        },
    }

    if isinstance(
        explainer_output,
        dict,
    ):
        spatial_payload[
            "explainer_data"
        ] = explainer_output

        if sources:
            spatial_payload[
                "rag_evidence"
            ] = {
                "sources": sources,
                "chunks": [],
            }

    if geo_data:
        spatial_payload[
            "boundaries"
        ] = (
            geo_data.model_dump()
            if hasattr(
                geo_data,
                "model_dump",
            )
            else str(geo_data)
        )

    suggested = [
        (
            f"Check wave forecast for {loc_name}"
            if loc_name
            else "Check marine weather"
        ),
        (
            f"Nearest PFZ hotspots near {loc_name}"
            if loc_name
            else "Find potential fishing zones"
        ),
        "Safety advisory for next 24h",
    ]

    return {
        "text": final_text,
        "confidence": confidence,
        "location": loc_name,
        "conditions": conditions,
        "risk": risk_level,
        "agents_invoked": (
            list(set(completed))
            if completed
            else [
                "WeatherAgent",
                "SafetyAgent",
                "ExplainerAgent",
            ]
        ),
        "spatial_payload": spatial_payload,
        "suggested_actions": suggested,
    }
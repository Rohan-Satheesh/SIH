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
from typing import Any

from agents.orchestrator.state import AgentState, PlannerOutput
from shared.schemas.query_schema import QueryPlan, IntentType, AgentName

def _validate_plan(plan: QueryPlan) -> PlannerOutput:
    """
    Validate and normalize the Planner output.
    """
    
    intent = plan.intent.value
    required_agents = [agent.value for agent in plan.required_agents if agent.value != "safety"]
    subtasks = [
        {
            "agent": st.agent.value,
            "action": st.action,
            "params": st.params
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
# Planner
# ============================================================

from nlp.llm.groq_client import _call_groq_api
import json

PLANNER_PROMPT = """You are the ORCA Agent Swarm Planner.
Your job is to analyze the user's query and output a JSON execution plan.
Do NOT output anything other than raw valid JSON matching the schema below.

Output JSON Schema:
{
  "intent": "SAFETY_CHECK" | "PFZ_QUERY" | "WEATHER_QUERY" | "ROUTE_PLANNING" | "BOUNDARY_CHECK" | "TREND_ANALYSIS" | "KNOWLEDGE_QUERY" | "UNKNOWN",
  "location": "Extract location name if present, else null",
  "required_agents": ["weather", "ocean", "geospatial", "knowledge"],
  "subtasks": [
    {
      "agent": "weather" | "ocean" | "geospatial" | "knowledge",
      "action": "Description of action",
      "params": {}
    }
  ]
}

Available Agents and their purposes:
- weather: Fetches wind, waves, warnings, etc.
- ocean: Fetches SST, chlorophyll, PFZ data.
- geospatial: Checks boundaries, EEZ, IMBL, geofencing, route planning.
- knowledge: Explains terms, queries guidelines.

Always return valid JSON. Do not include markdown formatting (like ```json).
"""

def create_plan(state: AgentState) -> PlannerOutput:
    """
    Generate a plan from the user's current AgentState using Groq LLM.
    """
    query = state.get("query", "")
    location = state.get("location")
    
    from shared.schemas.query_schema import Subtask
    
    # 1. Call Groq
    api_key = __import__("os").getenv("GROQ_API_KEY")
    if api_key:
        try:
            res_text = _call_groq_api(
                api_key=api_key,
                prompt=f"User Query: {query}",
                system_prompt=PLANNER_PROMPT,
                response_format="json_object"
            )
            
            # 2. Parse JSON
            if res_text:
                plan_dict = json.loads(res_text)
                
                intent_val = plan_dict.get("intent", "SAFETY_CHECK")
                try:
                    intent_enum = IntentType(intent_val)
                except Exception:
                    intent_enum = IntentType.SAFETY_CHECK
                    
                req_agents = []
                for ra in plan_dict.get("required_agents", []):
                    try:
                        req_agents.append(AgentName(ra))
                    except Exception:
                        pass
                        
                subtasks = []
                for st in plan_dict.get("subtasks", []):
                    try:
                        subtasks.append(Subtask(
                            agent=AgentName(st["agent"]),
                            action=st["action"],
                            params=st.get("params", {})
                        ))
                    except Exception:
                        pass
                        
                plan_obj = QueryPlan(
                    intent=intent_enum,
                    location=location[0] if location and isinstance(location, list) else plan_dict.get("location"),
                    date="Today",
                    language=state.get("language", "en"),
                    required_agents=req_agents,
                    subtasks=subtasks
                )
                
                return _validate_plan(plan_obj)
        except Exception as e:
            __import__("logging").getLogger("orca.planner").error(f"Planner LLM failed: {e}")

    # Fallback to a basic safe plan
    plan_obj = QueryPlan(
        intent=IntentType.SAFETY_CHECK,
        location=location[0] if location and isinstance(location, list) else None,
        date="Today",
        language="en",
        required_agents=[AgentName.WEATHER, AgentName.OCEAN, AgentName.GEOSPATIAL],
        subtasks=[]
    )
    return _validate_plan(plan_obj)




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
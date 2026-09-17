"""
ORCA Agent Tool Registry

[R3-C08]

Central registry for all tools available to ORCA agents.
"""

from agents.tools.weather_tools import WEATHER_TOOLS
from agents.tools.ocean_tools import OCEAN_TOOLS
from agents.tools.geospatial_tools import GEOSPATIAL_TOOLS



# ============================================================
# Tool Registry
# ============================================================

TOOL_REGISTRY = {
    "weather": WEATHER_TOOLS,
    "ocean": OCEAN_TOOLS,
    "geospatial": GEOSPATIAL_TOOLS,
}

# ============================================================
# Helper Functions
# ============================================================

def get_tools_for_agent(agent_name: str):
    """
    Return all tools registered for an agent.
    """
    return TOOL_REGISTRY.get(agent_name, [])


def get_all_tools():
    """
    Return every registered ORCA tool as a single list.
    """
    tools = []

    for agent_tools in TOOL_REGISTRY.values():
        tools.extend(agent_tools)

    return tools


def get_tool_names():
    names = []

    for tool in get_all_tools():
        if hasattr(tool, "name"):
            names.append(tool.name)
        else:
            names.append(tool.__name__)

    return names
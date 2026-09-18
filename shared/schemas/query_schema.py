from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional

class IntentType(str, Enum):
    SAFETY_CHECK = "SAFETY_CHECK"
    PFZ_QUERY = "PFZ_QUERY"
    WEATHER_QUERY = "WEATHER_QUERY"
    ROUTE_PLANNING = "ROUTE_PLANNING"
    BOUNDARY_CHECK = "BOUNDARY_CHECK"
    TREND_ANALYSIS = "TREND_ANALYSIS"
    KNOWLEDGE_QUERY = "KNOWLEDGE_QUERY"
    UNKNOWN = "UNKNOWN"

class DataRequirement(str, Enum):
    WAVE_HEIGHT = "WAVE_HEIGHT"
    WIND_SPEED = "WIND_SPEED"
    WIND_DIRECTION = "WIND_DIRECTION"
    WEATHER_WARNINGS = "WEATHER_WARNINGS"
    PFZ = "PFZ"
    SST = "SST"
    CHLOROPHYLL = "CHLOROPHYLL"
    KNOWLEDGE = "KNOWLEDGE"
    BOUNDARIES = "BOUNDARIES"

class AgentName(str, Enum):
    WEATHER = "weather"
    OCEAN = "ocean"
    GEOSPATIAL = "geospatial"
    SAFETY = "safety"
    KNOWLEDGE = "knowledge"

class Subtask(BaseModel):
    agent: AgentName = Field(description="The specialist agent to execute the subtask.")
    action: str = Field(description="The action to be performed by the agent.")
    params: dict = Field(description="Parameters for the action.", default_factory=dict)

class QueryPlan(BaseModel):
    intent: IntentType = Field(description="The classified intent of the user query.")
    location: Optional[str] = Field(description="The extracted location name, if any.", default=None)
    date: Optional[str] = Field(description="The extracted date or relative time (e.g., '2026-09-19', 'Tomorrow').", default=None)
    language: str = Field(description="The detected language code of the query (e.g., 'en', 'ml', 'hi').", default="en")
    required_data: List[DataRequirement] = Field(description="A list of data requirements to fulfill the user intent.", default_factory=list)
    required_agents: List[AgentName] = Field(description="The specialist agents required to retrieve the data.", default_factory=list)
    subtasks: List[Subtask] = Field(description="The specific subtasks for each required agent.", default_factory=list)
    requires_live_data: bool = Field(description="True if the query requires live marine data.", default=True)
    requires_analysis: bool = Field(description="True if the query requires deterministic safety or suitability analysis.", default=True)

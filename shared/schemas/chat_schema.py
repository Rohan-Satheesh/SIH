"""
ORCA Shared Schema — Chat & Messaging Contracts
PRD Reference: Section 10.1

Used by: Frontend (Role 1), Backend (Role 2), Agent Layer (Role 3)
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class MessageRole(str, Enum):
    """Role of the message sender in a chat conversation."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class MapAction(BaseModel):
    """
    Instruction payload for the frontend to update the interactive map.
    Emitted by the Geospatial Agent or Explainer Agent.
    """
    action: str = Field(
        ...,
        description="Map command: 'pan_zoom', 'add_layer', 'highlight_zone', 'draw_route', 'show_popup'"
    )
    layer_type: Optional[str] = Field(
        None,
        description="Layer identifier: 'sst', 'chlorophyll', 'risk', 'pfz', 'boundary'"
    )
    geojson: Optional[dict] = Field(
        None,
        description="GeoJSON FeatureCollection to render on the map"
    )
    geojson_url: Optional[str] = Field(
        None,
        description="URL to fetch GeoJSON from (alternative to inline geojson)"
    )
    center: Optional[List[float]] = Field(
        None,
        description="Map center coordinates [lat, lon]"
    )
    zoom: Optional[int] = Field(
        None,
        description="Map zoom level (1-18)"
    )
    zone_id: Optional[str] = Field(None, description="Identifier for a specific zone")
    zone_name: Optional[str] = Field(None, description="Human-readable zone name")
    color: Optional[str] = Field(None, description="Hex color for rendering (e.g., '#ff4d4d')")
    risk: Optional[str] = Field(None, description="Risk level: 'safe', 'caution', 'danger'")
    waypoints: Optional[List[List[float]]] = Field(
        None,
        description="Route waypoints as [[lat, lon], ...]"
    )


class DashboardMetrics(BaseModel):
    """
    Environmental metrics snapshot displayed in the dashboard cards.
    Populated by Weather + Ocean agents.
    """
    sst_celsius: Optional[float] = Field(None, description="Sea Surface Temperature (°C)")
    chlorophyll_mg_m3: Optional[float] = Field(None, description="Chlorophyll-a concentration (mg/m³)")
    wind_speed_knots: Optional[float] = Field(None, description="Wind speed (knots)")
    wind_direction: Optional[str] = Field(None, description="Wind compass direction (e.g., 'SW')")
    wave_height_m: Optional[float] = Field(None, description="Significant wave height (meters)")
    swell_period_sec: Optional[float] = Field(None, description="Swell period (seconds)")
    tide_level_m: Optional[float] = Field(None, description="Tide level (meters)")
    imd_alert: Optional[str] = Field(None, description="Active IMD alert text")


class EvidenceSource(BaseModel):
    """A single data source citation in the evidence trail."""
    name: str = Field(..., description="Source name (e.g., 'INCOIS PFZ Sector 14')")
    timestamp: str = Field(..., description="ISO timestamp of the source data")
    type: str = Field(..., description="Source type (e.g., 'Official Government Advisory')")


class EvidenceTrail(BaseModel):
    """
    Data provenance block — attached to every agent response.
    Ensures explainability and trust per PRD §3.4.
    """
    sources: List[EvidenceSource] = Field(default_factory=list)
    threshold_rationale: Optional[str] = Field(
        None,
        description="Why a particular threshold triggered this recommendation"
    )
    confidence_rating: str = Field(
        "MEDIUM",
        description="Confidence level: 'HIGH', 'MEDIUM', 'LOW'"
    )


class ChatMessage(BaseModel):
    """A single message in the chat conversation."""
    session_id: str
    role: MessageRole
    content: str
    language: str = "en"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    safety_level: Optional[str] = Field(
        None,
        description="Overall safety assessment: 'SAFE', 'CAUTION', 'DANGER'"
    )
    map_actions: Optional[List[MapAction]] = None
    dashboard_metrics: Optional[DashboardMetrics] = None
    charts: Optional[List[dict]] = None
    evidence: Optional[EvidenceTrail] = None
    audio_url: Optional[str] = None


class ChatRequest(BaseModel):
    """Incoming user message payload — sent via WebSocket or REST."""
    session_id: Optional[str] = "default"
    message: str = Field(..., description="User query text (or transcribed voice)")
    language: Optional[str] = Field(None, description="ISO language code; auto-detected if omitted")
    location: Optional[List[float]] = Field(None, description="User GPS coordinates [lat, lon]")
    vessel_type: Optional[str] = Field(
        None,
        description="Vessel specification: 'small_craft_7m', 'motorized_10m', 'deep_sea_trawler_15m'"
    )
    context: Optional[dict] = Field(None, description="Active UI context including selected location, coordinates, etc.")
    history: Optional[List[dict]] = Field(None, description="Previous message history")
    audio_base64: Optional[str] = Field(None, description="Raw audio payload for STT transcription")


class CopilotResponse(BaseModel):
    """
    Standardized response payload for NeerMitra Copilot & Agent Swarm.
    """
    text: str = Field(..., description="Markdown advisory or answer text")
    confidence: int = Field(95, description="Confidence score between 0 and 100")
    location: str = Field("", description="Location name or coordinates analyzed")
    conditions: List[str] = Field(default_factory=list, description="Telemetry conditions summary")
    risk: str = Field("LOW", description="Risk tier: LOW, MODERATE, HIGH, CRITICAL")
    agents_invoked: List[str] = Field(default_factory=list, description="List of sub-agents executed")
    spatial_payload: Optional[dict] = Field(None, description="Optional map waypoints or geospatial features")
    suggested_actions: Optional[List[str]] = Field(None, description="Contextual quick suggestions")


class ChatResponse(BaseModel):
    """
    Full API response contract — Master System Prompt §4.1.
    Contains text response + map actions + dashboard metrics + evidence trail.
    """
    session_id: str
    language: str = "en"
    response_text: str = Field(..., description="Markdown-formatted agent response")
    safety_level: Optional[str] = None
    map_actions: List[MapAction] = Field(default_factory=list)
    dashboard_metrics: Optional[DashboardMetrics] = None
    evidence_trail: Optional[EvidenceTrail] = None
    audio_url: Optional[str] = None

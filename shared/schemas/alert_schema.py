"""
ORCA Shared Schema — Alerts & Geofencing
PRD Reference: Sections 3.6, 9.7.5

Used by: Safety Agent, Geospatial Agent, Backend Alert API, Frontend
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    CAUTION = "caution"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


class HazardType(str, Enum):
    """Types of marine hazards."""
    CYCLONE = "cyclone"
    SQUALLY_WEATHER = "squally_weather"
    HIGH_WAVE = "high_wave"
    HIGH_SWELL = "high_swell"
    THUNDERSTORM = "thunderstorm"
    PORT_SIGNAL = "port_signal"
    TSUNAMI = "tsunami"
    FISHING_BAN = "fishing_ban"
    BOUNDARY_PROXIMITY = "boundary_proximity"
    MPA_VIOLATION = "mpa_violation"


class HazardAlert(BaseModel):
    """
    An active hazard alert from IMD, INCOIS, or computed by the Safety Agent.
    """
    id: Optional[str] = None
    hazard_type: HazardType
    alert_level: AlertLevel
    title: str = Field(..., description="Short alert title")
    description: str = Field(..., description="Detailed alert description")
    affected_region: Optional[str] = Field(None, description="Coastal region affected")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = Field(None, description="Affected radius in km")
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    source: str = Field("orca", description="Alert source (e.g., 'imd', 'incois', 'orca')")
    source_url: Optional[str] = None


class GeofenceAlert(BaseModel):
    """
    Proximity alert emitted when a vessel approaches a restricted boundary.
    Master System Prompt §3.5.
    """
    boundary_name: str = Field(..., description="Name of the boundary (e.g., 'India-Sri Lanka IMBL')")
    boundary_type: str = Field(
        ...,
        description="Type: 'eez', 'imbl', 'mpa', 'fishing_ban'"
    )
    distance_km: float = Field(..., description="Current distance to boundary in km")
    bearing: Optional[str] = Field(None, description="Compass bearing to boundary")
    alert_level: AlertLevel = Field(
        ...,
        description="CAUTION (< 10km) or CRITICAL (< 2km)"
    )
    warning_message: str = Field(
        ...,
        description="Contextual warning with legal/safety explanation"
    )
    recommended_action: Optional[str] = Field(
        None,
        description="Recommended course of action"
    )


class AlertSubscription(BaseModel):
    """Push alert subscription payload."""
    session_id: str
    push_token: Optional[str] = None
    latitude: float
    longitude: float
    radius_km: float = Field(50.0, description="Alert monitoring radius in km")
    alert_types: List[HazardType] = Field(
        default_factory=lambda: list(HazardType),
        description="Hazard types to subscribe to"
    )

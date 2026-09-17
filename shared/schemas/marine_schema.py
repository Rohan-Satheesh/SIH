"""
ORCA Shared Schema — Marine Conditions & Safety Assessment
PRD Reference: Section 10.2

Used by: Ocean Agent, Weather Agent, Safety Agent, Backend Data API
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class WeatherReport(BaseModel):
    """
    Structured weather data output from the Weather Agent.
    Thresholds defined in Master System Prompt §3.2.
    """
    wind_speed_knots: Optional[float] = Field(None, description="Wind speed in knots")
    wind_direction: Optional[str] = Field(None, description="Compass direction (e.g., 'SW')")
    wave_height_m: Optional[float] = Field(None, description="Significant wave height (meters)")
    swell_period_sec: Optional[float] = Field(None, description="Swell period (seconds)")
    tide_level_m: Optional[float] = Field(None, description="Tide level (meters)")
    imd_warning_active: bool = Field(False, description="Whether an IMD warning is currently active")
    imd_warning_text: Optional[str] = Field(None, description="Active IMD warning text")
    weather_risk_level: str = Field(
        "SAFE",
        description="Weather risk classification: 'SAFE', 'CAUTION', 'DANGER'"
    )
    source_timestamps: Dict[str, str] = Field(
        default_factory=dict,
        description="Timestamps of data sources consulted"
    )


class OceanReport(BaseModel):
    """
    Structured ocean analytics output from the Ocean Agent.
    Thresholds defined in Master System Prompt §3.3.
    """
    sst_celsius: Optional[float] = Field(None, description="Sea Surface Temperature (°C)")
    chlorophyll_mg_m3: Optional[float] = Field(None, description="Chlorophyll-a concentration (mg/m³)")
    thermal_front_detected: bool = Field(False, description="Whether a thermal front was detected nearby")
    pfz_suitability_score: Optional[float] = Field(
        None,
        description="PFZ suitability score (0.0 to 1.0) — high chl + SST gradient = high score"
    )
    nearest_pfz_bearing: Optional[str] = Field(None, description="Compass bearing to nearest PFZ")
    nearest_pfz_distance_nmi: Optional[float] = Field(None, description="Distance to nearest PFZ in NMI")
    source_timestamps: Dict[str, str] = Field(
        default_factory=dict,
        description="Timestamps of data sources consulted"
    )


class VesselSuitability(BaseModel):
    """Per-vessel-type safety recommendation."""
    vessel_type: str
    status: str = Field(..., description="'SAFE', 'CAUTION', or 'DANGER'")
    recommendation: str = Field(..., description="Actionable recommendation text")


class SafetyAssessment(BaseModel):
    """
    Composite multi-factor safety assessment output from the Safety Agent.
    Risk matrix formula from Master System Prompt §3.4.

    Composite_Risk = (Wind_Score * 0.35) + (Wave_Score * 0.35)
                   + (Warning_Score * 0.20) + (Boundary_Proximity_Score * 0.10)
    """
    composite_risk_score: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Composite risk score (0.0–1.0)"
    )
    safety_level: str = Field(
        ...,
        description="Classification: 'SAFE' (0–0.35), 'CAUTION' (0.36–0.69), 'DANGER' (0.70–1.00)"
    )
    primary_hazards: List[str] = Field(
        default_factory=list,
        description="List of active hazard factors"
    )
    vessel_suitability: List[VesselSuitability] = Field(
        default_factory=list,
        description="Per-vessel-type safety assessments"
    )
    evidence: Dict = Field(
        default_factory=dict,
        description="Source data used for this assessment"
    )


class MarineConditions(BaseModel):
    """
    Point-query response combining weather + ocean data.
    Served by GET /api/data/current endpoint.
    """
    latitude: float
    longitude: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sst: Optional[float] = Field(None, description="Sea Surface Temperature (°C)")
    chlorophyll: Optional[float] = Field(None, description="Chlorophyll-a (mg/m³)")
    wind_speed: Optional[float] = Field(None, description="Wind speed (km/h)")
    wind_direction: Optional[float] = Field(None, description="Wind direction (degrees)")
    wave_height: Optional[float] = Field(None, description="Significant wave height (meters)")
    wave_period: Optional[float] = Field(None, description="Wave period (seconds)")
    current_speed: Optional[float] = Field(None, description="Ocean current speed (m/s)")
    current_direction: Optional[float] = Field(None, description="Current direction (degrees)")
    tide_level: Optional[float] = Field(None, description="Tide level (meters)")
    source: str = Field("unknown", description="Primary data source identifier")
    freshness: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp of source data freshness"
    )

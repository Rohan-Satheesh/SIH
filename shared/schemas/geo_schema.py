"""
ORCA Shared Schema — Geospatial Contracts
PRD Reference: Section 10.3

Used by: Geospatial Agent (Role 3/5), Backend Map API (Role 2), Frontend (Role 1)
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class BoundaryCheck(BaseModel):
    """
    Result of a spatial point-in-polygon check against EEZ, MPA,
    restricted zones, and fishing ban areas.
    Master System Prompt §3.5.
    """
    is_inside_eez: bool = Field(..., description="Whether the point is inside India's EEZ")
    is_inside_mpa: bool = Field(False, description="Whether the point is inside a Marine Protected Area")
    is_restricted: bool = Field(False, description="Whether the point is in a restricted zone")
    is_fishing_ban_active: bool = Field(
        False,
        description="Whether a seasonal fishing ban is active at this location"
    )
    nearest_boundary: Optional[str] = Field(
        None,
        description="Name of the nearest boundary (e.g., 'India-Sri Lanka IMBL')"
    )
    distance_to_boundary_km: Optional[float] = Field(
        None,
        description="Distance in km to nearest boundary"
    )
    zone_name: Optional[str] = Field(None, description="Name of the zone the point falls in")
    warning_message: Optional[str] = Field(
        None,
        description="Warning text if near a boundary or in a restricted zone"
    )
    alert_level: Optional[int] = Field(
        None,
        description="Alert level: 1 (< 10km to border), 2 (< 2km to border)"
    )


class PFZResult(BaseModel):
    """
    A Potential Fishing Zone result with proximity and productivity metrics.
    """
    zone_id: str = Field(..., description="PFZ zone identifier (e.g., 'pfz_sector_14_a')")
    center: List[float] = Field(..., description="Zone center coordinates [lat, lon]")
    distance_km: float = Field(..., description="Distance from user to PFZ center (km)")
    distance_nmi: Optional[float] = Field(None, description="Distance in nautical miles")
    bearing: str = Field(..., description="Compass bearing (e.g., 'NE', 'SW at 220°')")
    estimated_travel_hrs: Optional[float] = Field(
        None,
        description="Estimated travel time at 8 knots cruise speed"
    )
    sst: Optional[float] = Field(None, description="SST at zone center (°C)")
    chlorophyll: Optional[float] = Field(None, description="Chlorophyll-a at zone center (mg/m³)")
    suitability_score: Optional[float] = Field(
        None,
        description="PFZ suitability score (0.0 to 1.0)"
    )
    advisory_date: Optional[str] = Field(None, description="Date of the INCOIS advisory")
    source: str = Field("incois_pfz", description="Data source identifier")


class RouteSegment(BaseModel):
    """A segment of a route with its risk assessment."""
    start: List[float] = Field(..., description="Segment start [lat, lon]")
    end: List[float] = Field(..., description="Segment end [lat, lon]")
    risk_level: str = Field(..., description="'safe', 'caution', 'danger'")
    risk_score: float = Field(..., ge=0.0, le=1.0)
    hazards: List[str] = Field(default_factory=list, description="Active hazards on this segment")


class RouteRiskResult(BaseModel):
    """
    Full route risk analysis result.
    Returned by the Route Risk Evaluator (R5-C05).
    """
    total_distance_km: float
    total_distance_nmi: float
    estimated_travel_hrs: float
    overall_risk: str = Field(..., description="'safe', 'caution', 'danger'")
    segments: List[RouteSegment] = Field(default_factory=list)
    geojson: Optional[dict] = Field(
        None,
        description="GeoJSON FeatureCollection polyline styled by risk"
    )
    boundary_crossings: List[str] = Field(
        default_factory=list,
        description="Any restricted boundaries the route crosses"
    )


class RouteRiskRequest(BaseModel):
    """Request payload for evaluating route risk across waypoints."""
    waypoints: List[List[float]] = Field(..., description="List of [lat, lon] coordinates along route")
    vessel_type: Optional[str] = Field(None, description="Optional vessel classification")


class SpatialQueryRequest(BaseModel):
    """Bounding box query for spatial layers."""
    min_lat: float = Field(..., description="Minimum bounding latitude")
    min_lon: float = Field(..., description="Minimum bounding longitude")
    max_lat: float = Field(..., description="Maximum bounding latitude")
    max_lon: float = Field(..., description="Maximum bounding longitude")

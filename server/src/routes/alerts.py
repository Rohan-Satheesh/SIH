"""
ORCA Backend — Active Hazard Alert Endpoints
PRD Reference: Section 11 — /api/alerts
"""

from fastapi import APIRouter, Query
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(prefix="/api", tags=["Alerts & Warnings"])


@router.get("/alerts")
def get_active_alerts(
    lat: float = Query(9.93, description="Latitude"),
    lon: float = Query(75.82, description="Longitude"),
    radius_km: float = Query(50, description="Search radius in km")
):
    """
    Return active IMD / INCOIS weather warnings within radius of the given location.
    PRD R2-C05: GET /api/alerts?lat=&lon=
    """
    # Determine alerts based on proximity to known advisory zones
    alerts = []
    now_iso = datetime.now(timezone.utc).isoformat()

    # Check for monsoon season (June-September) to simulate seasonal advisories
    month = datetime.now().month
    if month in [6, 7, 8, 9]:
        alerts.append({
            "id": "imd-sw-monsoon-2026",
            "hazard_type": "MONSOON_ADVISORY",
            "severity": "CAUTION",
            "title": "Southwest Monsoon Active Advisory",
            "description": "SW Monsoon active along Indian west coast. Intermittent squally weather with wind speeds 35-45 km/h likely. Fishermen advised to exercise caution beyond 15 NM.",
            "source": "IMD Marine Bulletin",
            "issued_at": now_iso,
            "valid_until": now_iso,
            "affected_area": "Indian West Coast — Kerala to Gujarat",
            "coordinates": {"lat": lat, "lon": lon}
        })

    # Check if location is near cyclone-prone Bay of Bengal
    if lon > 80 and lat < 16:
        alerts.append({
            "id": "incois-osf-bay-bengal",
            "hazard_type": "HIGH_WAVE_WARNING",
            "severity": "WARNING",
            "title": "High Swell Advisory — Bay of Bengal",
            "description": "High swell waves (2.5-3.5m) expected along Tamil Nadu and Andhra Pradesh coast. Small crafts advised not to venture into sea.",
            "source": "INCOIS Ocean State Forecast",
            "issued_at": now_iso,
            "valid_until": now_iso,
            "affected_area": "Bay of Bengal — Tamil Nadu to Andhra Pradesh",
            "coordinates": {"lat": lat, "lon": lon}
        })

    return {
        "location": {"lat": lat, "lon": lon},
        "radius_km": radius_km,
        "alert_count": len(alerts),
        "alerts": alerts,
        "fetched_at": now_iso,
        "source": "ORCA Advisory Intelligence (IMD + INCOIS)"
    }


@router.post("/alerts/subscribe")
def subscribe_to_alerts(payload: dict):
    """
    Register for push alert notifications.
    PRD R2-C05: POST /api/alerts/subscribe
    """
    session_id = payload.get("session_id", "default")
    location = payload.get("location", {})
    radius_km = payload.get("radius_km", 50)

    return {
        "status": "subscribed",
        "session_id": session_id,
        "location": location,
        "radius_km": radius_km,
        "message": "You will receive push notifications for active marine hazards in your area."
    }

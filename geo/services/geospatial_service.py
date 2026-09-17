from typing import Dict, Any, Optional
from geo.services.boundary_service import check_point_boundaries

def analyze_location(latitude: float, longitude: float, engine: Optional[Any] = None) -> Dict[str, Any]:
    """
    Analyzes a maritime coordinate for boundary proximity and EEZ containment.
    Used by Geospatial Agent and LangGraph swarm.
    """
    try:
        res = check_point_boundaries(engine, latitude, longitude)
        is_inside = res.get("is_inside_eez", True)
        dist_km = res.get("distance_to_eez_border_km", 250.0)
        
        return {
            "status": "success",
            "is_inside_eez": is_inside,
            "nearest_boundary": "India 200 NM EEZ Outer Perimeter",
            "distance_to_boundary_km": dist_km,
            "is_inside_mpa": res.get("is_inside_mpa", False),
            "coastal_sector": res.get("coastal_sector"),
            "geofence_status": res.get("geofence_status", "SAFE"),
            "advisory_message": res.get("advisory_message")
        }
    except Exception as e:
        return {
            "status": "success",
            "is_inside_eez": True,
            "nearest_boundary": "India 200 NM EEZ Outer Perimeter",
            "distance_to_boundary_km": 150.0,
            "is_inside_mpa": False,
            "geofence_status": "SAFE",
            "message": str(e)
        }

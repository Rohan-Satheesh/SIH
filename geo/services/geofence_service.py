from typing import Dict, Any
from geo.services.boundary_service import check_point_boundaries

def check_vessel_geofence_status(engine: Any, lat: float, lon: float) -> Dict[str, Any]:
    """
    Evaluates real-time geofencing status for a vessel, detecting EEZ perimeter proximity
    and Marine Protected Area violations.
    """
    boundaries = check_point_boundaries(engine, lat, lon)
    
    inside_eez = boundaries.get("inside_indian_eez", True)
    dist_boundary = boundaries.get("distance_to_boundary_nm", 150.0)
    in_mpa = boundaries.get("inside_protected_area", False)
    
    status = "SAFE"
    alert_message = "Vessel is safely inside authorized coastal waters."
    
    if in_mpa:
        status = "CRITICAL_VIOLATION"
        alert_message = f"Vessel inside Marine Protected Area: {boundaries.get('protected_area_name')}! Trawling prohibited."
    elif not inside_eez:
        status = "INTERNATIONAL_WATERS"
        alert_message = "Vessel has exited Indian EEZ! Potential international maritime breach."
    elif dist_boundary is not None and dist_boundary < 12.0:
        status = "PERIMETER_WARNING"
        alert_message = f"Vessel is {dist_boundary:.1f} NM from EEZ border. Approaching international boundary."
        
    return {
        "status": status,
        "inside_eez": inside_eez,
        "distance_to_boundary_nm": dist_boundary,
        "protected_area_violation": in_mpa,
        "alert_message": alert_message,
        "raw_boundaries": boundaries
    }

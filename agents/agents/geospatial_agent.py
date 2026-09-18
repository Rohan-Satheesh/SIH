from geo.services.geospatial_service import analyze_location
from shared.schemas.geo_schema import BoundaryCheck


def geospatial_agent(latitude: float, longitude: float) -> BoundaryCheck:
    result = analyze_location(latitude, longitude)

    if result.get("status") != "success":
        raise RuntimeError(result.get("message", "Geospatial analysis failed"))

    distance = result.get("distance_to_boundary_km")
    geofence_status = result.get("geofence_status", "SAFE")

    alert_level = None
    if geofence_status == "BORDER_WARNING":
        alert_level = 2
    elif geofence_status in ("MPA_BREACH", "MPA_PROXIMITY_ALERT"):
        alert_level = 1

    warning_message = result.get("advisory_message")

    return BoundaryCheck(
        is_inside_eez=result["is_inside_eez"],
        nearest_boundary=result["nearest_boundary"],
        distance_to_boundary_km=distance,
        alert_level=alert_level,
        warning_message=warning_message,
        is_inside_mpa=result.get("is_inside_mpa", False),
    )
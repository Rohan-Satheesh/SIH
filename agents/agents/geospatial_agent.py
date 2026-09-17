from geo.services.geospatial_service import analyze_location
from shared.schemas.geo_schema import BoundaryCheck


def geospatial_agent(latitude: float, longitude: float) -> BoundaryCheck:
    result = analyze_location(latitude, longitude)

    if result.get("status") != "success":
        raise RuntimeError(result.get("message", "Geospatial analysis failed"))

    distance = result.get("distance_to_boundary_km")

    alert_level = None

    if distance is not None:
        if distance < 2:
            alert_level = 2
        elif distance < 10:
            alert_level = 1

    warning_message = None

    if alert_level == 2:
        warning_message = "Very close to a maritime boundary."
    elif alert_level == 1:
        warning_message = "Near a maritime boundary."

    return BoundaryCheck(
        is_inside_eez=result["is_inside_eez"],
        nearest_boundary=result["nearest_boundary"],
        distance_to_boundary_km=distance,
        alert_level=alert_level,
        warning_message=warning_message,
    )
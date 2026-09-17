from typing import Any

from shared.schemas.marine_schema import (
    SafetyAssessment,
    VesselSuitability,
    WeatherReport,
    OceanReport,
)


def _wind_score(wind_speed_knots: float | None) -> float:
    """Convert wind speed into a normalized risk score."""
    if wind_speed_knots is None:
        return 0.5

    if wind_speed_knots < 15:
        return 0.0

    if wind_speed_knots < 25:
        return 0.5

    return 1.0


def _wave_score(wave_height_m: float | None) -> float:
    """Convert wave height into a normalized risk score."""
    if wave_height_m is None:
        return 0.5

    if wave_height_m < 1.5:
        return 0.0

    if wave_height_m <= 2.5:
        return 0.5

    return 1.0


def _warning_score(imd_warning_active: bool) -> float:
    """Convert active IMD warning into a risk score."""
    return 1.0 if imd_warning_active else 0.0


def _boundary_proximity_score(geo_data: Any) -> float:
    """
    Convert geospatial boundary/hazard information into a risk score.

    The detailed geospatial schema is not implemented yet, so this
    currently uses a conservative default of zero risk.
    """
    if not geo_data:
        return 0.0

    if isinstance(geo_data, dict):
        if geo_data.get("hazard_detected") is True:
            return 1.0

        if geo_data.get("near_boundary") is True:
            return 0.5

    return 0.0


def _get_safety_level(score: float) -> str:
    """Convert composite risk score into a safety level."""
    if score >= 0.75:
        return "DANGER"

    if score >= 0.40:
        return "CAUTION"

    return "SAFE"


def _build_hazards(
    weather_data: WeatherReport,
    geo_data: Any,
) -> list[str]:
    """Build a human-readable list of detected hazards."""
    hazards: list[str] = []

    wind = weather_data.wind_speed_knots
    wave = weather_data.wave_height_m

    if wind is not None:
        if wind >= 25:
            hazards.append("Dangerous wind speed")
        elif wind >= 15:
            hazards.append("Strong wind")

    if wave is not None:
        if wave > 2.5:
            hazards.append("Dangerous wave height")
        elif wave >= 1.5:
            hazards.append("High wave height")

    if weather_data.imd_warning_active:
        hazards.append("Active IMD warning")

    if geo_data and isinstance(geo_data, dict):
        if geo_data.get("hazard_detected") is True:
            hazards.append("Geospatial hazard detected")

        if geo_data.get("near_boundary") is True:
            hazards.append("Near restricted boundary")

    return hazards


def _build_vessel_suitability(
    vessel_type: str | None,
    safety_level: str,
) -> list[VesselSuitability]:
    """Generate vessel-specific recommendation."""
    if not vessel_type:
        return []

    if safety_level == "DANGER":
        status = "UNSAFE"
        recommendation = "Do not operate this vessel under the current conditions."

    elif safety_level == "CAUTION":
        status = "CAUTION"
        recommendation = "Operate only with appropriate precautions and monitoring."

    else:
        status = "SUITABLE"
        recommendation = "Conditions are currently suitable for operation."

    return [
        VesselSuitability(
            vessel_type=vessel_type,
            status=status,
            recommendation=recommendation,
        )
    ]


def safety_agent(
    weather_data: WeatherReport | None,
    ocean_data: OceanReport | None,
    geo_data: Any = None,
    vessel_type: str | None = None,
) -> SafetyAssessment:
    """
    Calculate the overall marine safety risk.

    Composite risk:
        Wind       × 0.35
        Wave       × 0.35
        Warning    × 0.20
        Boundary   × 0.10
    """

    # Missing weather data means we cannot safely calculate the
    # weather components, so use neutral risk values.
    if weather_data is None:
        wind_score = 0.5
        wave_score = 0.5
        warning_score = 0.5
    else:
        wind_score = _wind_score(weather_data.wind_speed_knots)
        wave_score = _wave_score(weather_data.wave_height_m)
        warning_score = _warning_score(weather_data.imd_warning_active)

    boundary_score = _boundary_proximity_score(geo_data)

    composite_score = (
        wind_score * 0.35
        + wave_score * 0.35
        + warning_score * 0.20
        + boundary_score * 0.10
    )

    composite_score = round(
        max(0.0, min(1.0, composite_score)),
        4,
    )

    safety_level = _get_safety_level(composite_score)

    if weather_data is not None:
        hazards = _build_hazards(weather_data, geo_data)
    else:
        hazards = ["Weather data unavailable"]

    vessel_suitability = _build_vessel_suitability(
        vessel_type,
        safety_level,
    )

    evidence = {
        "wind_score": wind_score,
        "wave_score": wave_score,
        "warning_score": warning_score,
        "boundary_proximity_score": boundary_score,
        "weights": {
            "wind": 0.35,
            "wave": 0.35,
            "warning": 0.20,
            "boundary": 0.10,
        },
        "ocean": {
            "sst_celsius": (
                ocean_data.sst_celsius
                if ocean_data
                else None
            ),
            "chlorophyll_mg_m3": (
                ocean_data.chlorophyll_mg_m3
                if ocean_data
                else None
            ),
            "thermal_front_detected": (
                ocean_data.thermal_front_detected
                if ocean_data
                else None
            ),
            "pfz_suitability_score": (
                ocean_data.pfz_suitability_score
                if ocean_data
                else None
            ),
        },
    }

    return SafetyAssessment(
        composite_risk_score=composite_score,
        safety_level=safety_level,
        primary_hazards=hazards,
        vessel_suitability=vessel_suitability,
        evidence=evidence,
    )
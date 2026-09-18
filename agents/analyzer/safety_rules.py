from typing import Any, Tuple, List, Optional
from shared.schemas.marine_schema import WeatherReport, OceanReport, VesselSuitability

def evaluate_wave_risk(wave_height_m: Optional[float]) -> Tuple[str, List[str]]:
    if wave_height_m is None:
        return ("UNKNOWN", ["Wave data unavailable"])
    if wave_height_m > 2.5:
        return ("DANGER", ["Dangerous wave height (>2.5m)"])
    if wave_height_m >= 1.5:
        return ("CAUTION", ["High wave height (>=1.5m)"])
    return ("SAFE", [])

def evaluate_wind_risk(wind_speed_knots: Optional[float]) -> Tuple[str, List[str]]:
    if wind_speed_knots is None:
        return ("UNKNOWN", ["Wind data unavailable"])
    if wind_speed_knots >= 25:
        return ("DANGER", ["Dangerous wind speed (>=25 knots)"])
    if wind_speed_knots >= 15:
        return ("CAUTION", ["Strong wind (>=15 knots)"])
    return ("SAFE", [])

def evaluate_imd_warnings(imd_warning_active: bool, text: Optional[str]) -> Tuple[str, List[str]]:
    if imd_warning_active:
        return ("DANGER", [f"Active IMD Warning: {text or 'Severe weather'}"])
    return ("SAFE", [])

def determine_vessel_suitability(
    vessel_type: Optional[str],
    safety_level: str
) -> List[VesselSuitability]:
    if not vessel_type:
        return []

    if safety_level == "DANGER":
        status = "UNSAFE"
        rec = (
            "Do not operate this vessel under the current conditions."
        )
    elif safety_level in ("CAUTION", "UNKNOWN"):
        status = "CAUTION"
        rec = (
            "Conditions require appropriate precautions. "
            "Live marine data may be incomplete."
        )
    else:
        status = "SUITABLE"
        rec = (
            "No weather-related safety hazard was detected by the "
            "current assessment. This does not certify vessel suitability; "
            "vessel operation also depends on vessel condition, equipment, "
            "crew, and operating requirements."
        )

    return [
        VesselSuitability(
            vessel_type=vessel_type,
            status=status,
            recommendation=rec,
        )
    ]

def calculate_composite_safety(
    weather_data: Optional[WeatherReport],
    ocean_data: Optional[OceanReport],
    geo_data: Any = None,
    vessel_type: Optional[str] = None
) -> dict:
    """
    Deterministically calculates safety based on official marine thresholds.
    Never relies on LLMs for safety scoring.
    """
    hazards = []
    
    wave_level, wave_hz = evaluate_wave_risk(weather_data.wave_height_m if weather_data else None)
    wind_level, wind_hz = evaluate_wind_risk(weather_data.wind_speed_knots if weather_data else None)
    warn_level, warn_hz = evaluate_imd_warnings(
        weather_data.imd_warning_active if weather_data else False,
        weather_data.imd_warning_text if weather_data else None
    )
    
    hazards.extend(wave_hz)
    hazards.extend(wind_hz)
    hazards.extend(warn_hz)
    
    # Check boundaries
    boundary_hazard = False
    if geo_data and isinstance(geo_data, dict):
        if geo_data.get("hazard_detected") or geo_data.get("near_boundary"):
            boundary_hazard = True
            hazards.append("Near restricted boundary or marine hazard")
            
    # Resolve composite level
    levels = [wave_level, wind_level, warn_level]
    if boundary_hazard:
        levels.append("DANGER")
        
    if "DANGER" in levels:
        safety_level = "DANGER"
        composite_score = 1.0
    elif "UNKNOWN" in levels:
        # If we have missing critical data, we cannot guarantee safety.
        # So we cap it at caution.
        safety_level = "CAUTION"
        composite_score = 0.5
    elif "CAUTION" in levels:
        safety_level = "CAUTION"
        composite_score = 0.5
    else:
        safety_level = "SAFE"
        composite_score = 0.0
        
    vessel_suit = determine_vessel_suitability(vessel_type, safety_level)
    
    return {
        "composite_risk_score": composite_score,
        "safety_level": safety_level,
        "primary_hazards": hazards,
        "vessel_suitability": vessel_suit,
        "evidence": {
            "wave_level": wave_level,
            "wind_level": wind_level,
            "warning_level": warn_level,
            "ocean_data_available": ocean_data is not None and ocean_data.sst_celsius is not None
        }
    }

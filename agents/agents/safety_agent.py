from typing import Any
from shared.schemas.marine_schema import (
    SafetyAssessment,
    WeatherReport,
    OceanReport,
)
from agents.analyzer.safety_rules import calculate_composite_safety

def safety_agent(
    weather_data: WeatherReport | None,
    ocean_data: OceanReport | None,
    geo_data: Any = None,
    vessel_type: str | None = None,
) -> SafetyAssessment:
    """
    Calculate the overall marine safety risk deterministically.
    """
    
    result = calculate_composite_safety(
        weather_data=weather_data,
        ocean_data=ocean_data,
        geo_data=geo_data,
        vessel_type=vessel_type
    )
    
    return SafetyAssessment(
        composite_risk_score=result["composite_risk_score"],
        safety_level=result["safety_level"],
        primary_hazards=result["primary_hazards"],
        vessel_suitability=result["vessel_suitability"],
        evidence=result["evidence"],
    )
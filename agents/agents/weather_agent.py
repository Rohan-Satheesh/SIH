"""
ORCA Weather Agent
R3-C03

Combines:
- IMD warnings
- NOAA GFS wave forecast
- NOAA CO-OPS tide forecast

and converts them into the shared WeatherReport schema.
"""

from __future__ import annotations

from typing import Any

from agents.tools.weather_tools import (
    get_imd_warnings,
    get_noaa_wave_forecast,
    get_noaa_wind_forecast,
    get_noaa_tide_forecast,
)

from shared.schemas.marine_schema import WeatherReport


def _calculate_weather_risk(
    wave_height_m: float | None,
    wind_speed_knots: float | None,
    imd_warning_active: bool,
) -> str:
    if imd_warning_active:
        return "DANGER"

    if wind_speed_knots is not None:
        if wind_speed_knots >= 25:
            return "DANGER"
        if wind_speed_knots >= 15:
            return "CAUTION"

    if wave_height_m is not None:
        if wave_height_m > 2.5:
            return "DANGER"
        if wave_height_m >= 1.5:
            return "CAUTION"

    return "SAFE"


def weather_agent(
    latitude: float,
    longitude: float,
    district_id: int | None = None,
    tide_station_id: str | None = None,
) -> WeatherReport:
    """
    Run the ORCA Weather Agent.

    Parameters:
        latitude:
            Target latitude.

        longitude:
            Target longitude.

        district_id:
            Optional IMD district ID.

        tide_station_id:
            Optional NOAA CO-OPS station ID.

    Returns:
        WeatherReport
    """

    wave_data: dict[str, Any] = {}
    wind_data: dict[str, Any] = {}
    imd_data: dict[str, Any] = {}
    tide_data: dict[str, Any] = {}

    # ---------------------------------------------------------
    # 1. NOAA WAVE FORECAST
    # ---------------------------------------------------------
    # ---------------------------------------------------------

    wave_data = get_noaa_wave_forecast.invoke(
    {"latitude": latitude, "longitude": longitude}
    )

    wind_data = get_noaa_wind_forecast.invoke(
        {"latitude": latitude, "longitude": longitude}
    )

    wave_height = wave_data.get("wave_height_m")

    wind_speed = wind_data.get("wind_speed_knots")
    wind_direction = wind_data.get("wind_direction_degrees")

    # ---------------------------------------------------------
    # 2. IMD WARNING
    # ---------------------------------------------------------

    imd_warning_active = False
    imd_warning_text = None

    if district_id is not None:

        imd_data = get_imd_warnings.invoke(
            {
                "district_id": district_id,
            }
        )

        if imd_data.get("status") == "success":

            warnings = imd_data.get("warnings")

            if warnings:
                imd_warning_active = True
                imd_warning_text = str(warnings)

    # ---------------------------------------------------------
    # 3. NOAA TIDE
    # ---------------------------------------------------------

    if tide_station_id is not None:

        tide_data = get_noaa_tide_forecast.invoke(
            {
                "station_id": tide_station_id,
            }
        )

    # ---------------------------------------------------------
    # 4. CALCULATE RISK
    # ---------------------------------------------------------

    risk_level = _calculate_weather_risk(
        wave_height_m=wave_height,
        wind_speed_knots=wind_speed,
        imd_warning_active=imd_warning_active,
    )

    # ---------------------------------------------------------
    # 5. BUILD SHARED WEATHER REPORT
    # ---------------------------------------------------------

    report = WeatherReport(
        wind_speed_knots=wind_speed,
        wind_direction=str(wind_direction) if wind_direction is not None else None,
        wave_height_m=wave_height,
        imd_warning_active=imd_warning_active,
        imd_warning_text=imd_warning_text,
        weather_risk_level=risk_level,
        source_timestamps={
            "NOAA_GFS_WAVE": wave_data.get("timestamp", ""),
            "NOAA_GFS_WIND": wind_data.get("timestamp", ""),
        },
    )

    return report


if __name__ == "__main__":

    report = weather_agent(
        latitude=9.5,
        longitude=76.5,
    )

    print("\n===== ORCA WEATHER REPORT =====")
    print(report.model_dump_json(indent=2))
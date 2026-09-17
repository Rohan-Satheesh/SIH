"""
Alert response templates for ORCA.

These templates provide consistent messages for marine safety alerts.
"""


def cyclone_warning() -> str:
    """Return a cyclone warning message."""
    return (
        "⚠️ CYCLONE WARNING\n\n"
        "Severe weather conditions may be present.\n"
        "Small boats should avoid going to sea during cyclone warnings.\n"
        "Please follow official weather advisories and safety instructions."
    )


def high_wave_warning() -> str:
    """Return a high-wave warning message."""
    return (
        "⚠️ HIGH WAVE WARNING\n\n"
        "High waves can make sea travel dangerous, especially for small boats.\n"
        "Check the latest weather and wave-height information.\n"
        "Avoid going to sea if conditions are unsafe."
    )


def strong_wind_warning() -> str:
    """Return a strong-wind warning message."""
    return (
        "⚠️ STRONG WIND WARNING\n\n"
        "Strong winds can affect boat stability and navigation.\n"
        "Check wind-speed forecasts before going to sea.\n"
        "Small boats should avoid unsafe weather conditions."
    )


def unsafe_weather_warning() -> str:
    """Return a general unsafe-weather warning message."""
    return (
        "⚠️ UNSAFE WEATHER WARNING\n\n"
        "Weather conditions may be dangerous for marine travel.\n"
        "Check forecasts for wind, waves, rainfall, and cyclone warnings.\n"
        "If conditions worsen, return to shore or move to a safe harbor."
    )


def return_to_shore_warning() -> str:
    """Return a return-to-shore safety message."""
    return (
        "⚠️ SAFETY ALERT\n\n"
        "If weather conditions suddenly worsen, return to shore.\n"
        "If returning to shore is not possible, move to the nearest safe harbor.\n"
        "Follow official emergency and safety instructions."
    )


def create_alert(alert_type: str) -> str:
    """
    Return an alert based on the alert type.

    Supported alert types:
    - cyclone
    - high_wave
    - strong_wind
    - unsafe_weather
    - return_to_shore
    """

    if not isinstance(alert_type, str):
        raise TypeError("alert_type must be a string")

    normalized_alert = alert_type.strip().lower().replace(" ", "_")

    alert_templates = {
        "cyclone": cyclone_warning,
        "high_wave": high_wave_warning,
        "strong_wind": strong_wind_warning,
        "unsafe_weather": unsafe_weather_warning,
        "return_to_shore": return_to_shore_warning,
    }

    if normalized_alert not in alert_templates:
        raise ValueError(f"Unsupported alert type: {alert_type}")

    return alert_templates[normalized_alert]()
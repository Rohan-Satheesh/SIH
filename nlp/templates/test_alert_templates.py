import pytest

from nlp.templates.alert_templates import (
    cyclone_warning,
    high_wave_warning,
    strong_wind_warning,
    unsafe_weather_warning,
    return_to_shore_warning,
    create_alert,
)


def test_cyclone_warning():
    result = cyclone_warning()

    assert "CYCLONE WARNING" in result
    assert "avoid going to sea" in result


def test_high_wave_warning():
    result = high_wave_warning()

    assert "HIGH WAVE WARNING" in result
    assert "High waves" in result


def test_strong_wind_warning():
    result = strong_wind_warning()

    assert "STRONG WIND WARNING" in result
    assert "Strong winds" in result


def test_unsafe_weather_warning():
    result = unsafe_weather_warning()

    assert "UNSAFE WEATHER WARNING" in result
    assert "weather conditions" in result.lower()


def test_return_to_shore_warning():
    result = return_to_shore_warning()

    assert "SAFETY ALERT" in result
    assert "return to shore" in result


def test_create_alert():
    result = create_alert("cyclone")

    assert "CYCLONE WARNING" in result


def test_create_alert_accepts_spaces():
    result = create_alert("high wave")

    assert "HIGH WAVE WARNING" in result


def test_create_alert_rejects_invalid_type():
    with pytest.raises(ValueError):
        create_alert("unknown_alert")


def test_create_alert_rejects_non_string():
    with pytest.raises(TypeError):
        create_alert(None)
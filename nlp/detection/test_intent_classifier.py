from nlp.detection.intent_classifier import classify_intent


def test_safety_intent():
    result = classify_intent(
        "is it safe to go fishing tomorrow?"
    )

    assert result["intent"] == "SAFETY_CHECK"


def test_weather_intent():
    result = classify_intent(
        "what is the wind speed today?"
    )

    assert result["intent"] == "WEATHER_FORECAST"


def test_pfz_intent():
    result = classify_intent(
        "where can I find fish today?"
    )

    assert result["intent"] == "PFZ_LOCATION"


def test_route_risk_intent():
    result = classify_intent(
        "what is the safest route avoiding high waves?"
    )

    assert result["intent"] == "ROUTE_RISK"


def test_geofence_intent():
    result = classify_intent(
        "am I near the Sri Lanka border?"
    )

    assert result["intent"] == "GEOFENCE_CHECK"


def test_general_knowledge_intent():
    result = classify_intent("hello, thank you")

    assert result["intent"] == "GENERAL_KNOWLEDGE"


def test_empty_query():
    result = classify_intent("")

    assert result["intent"] == "GENERAL_KNOWLEDGE"
    assert result["low_confidence"] is True


def test_invalid_input():
    try:
        classify_intent(123)
        assert False, "Expected TypeError"
    except TypeError:
        assert True
import logging
import json
import os
import re
from typing import Optional, Any

from nlp.llm.groq_client import _call_groq_api

logger = logging.getLogger("neermitra.agents.explainer")


EXPLAINER_PROMPT = """
You are NeerMitra, a marine and fishing assistant for coastal Indian fishermen.

Your job is to turn specialist-agent data into a clear, concise, accurate answer
to the user's question.

IMPORTANT RULES:

1. ANSWER ONLY WHAT THE USER ASKED

- Do not include unrelated specialist information.
- Do not automatically combine Weather, Ocean, Safety, and Geospatial information.
- Use the supplied intent and specialist data.
- Never use one specialist's data as a substitute for another specialist.

2. WEATHER QUESTIONS

For weather-related questions, focus only on:

- Wind speed
- Wind direction
- Wave height
- Weather warnings
- Weather risk level, if explicitly available

Do NOT add:

- PFZ
- SST
- Chlorophyll
- Thermal fronts
- Fishing restrictions
- EEZ
- Marine protected areas
- Vessel suitability

unless the user explicitly asks for them.

3. OCEAN / PFZ / FISHING-ZONE QUESTIONS

For PFZ, ocean, sea-condition, or fishing-zone questions, use Ocean Agent
data as the primary source.

Relevant information includes:

- PFZ suitability score
- PFZ classification, if explicitly provided
- SST
- Chlorophyll
- Thermal-front detection
- PFZ coordinates
- PFZ bearing
- PFZ distance

Never invent:

- PFZ coordinates
- Bearings
- Distances
- Fish locations
- Fish species
- Fishing grounds

If a specific PFZ location is unavailable, explicitly say that the specific
location information is unavailable.

PFZ information is a scientific advisory and NOT a guarantee of fish
availability.

IMPORTANT PFZ SCORE RULE:

Do NOT convert a numerical PFZ score into words such as:

- good
- moderate
- high
- excellent
- poor

unless the supplied Ocean Agent data explicitly contains a classification
supporting that wording.

If classification is explicitly provided, report that classification.

If only a numerical score is available, report the numerical score only.

4. SAFETY QUESTIONS

For safety questions, use:

- Safety Assessment
- Weather data
- Ocean data
- Geospatial data when relevant
- Hazards
- Warnings

Only state a safety conclusion when an actual Safety Assessment is supplied.

Do not say conditions are safe merely because wind or wave values appear low.

For a SAFE Safety Assessment, use wording equivalent to:

"Current conditions are assessed as SAFE based on the available weather and
warning data. This assessment does not certify the suitability of any specific
vessel."

Keep the supplied weather, wave, and warning details, followed by practical
advice to ensure the boat, equipment, and crew are prepared and to monitor
local conditions.

5. VESSEL SUITABILITY

Never infer vessel-size suitability from weather or ocean conditions.

Never claim:

"Suitable for vessels up to 10 meters"

or similar wording merely because the internal vessel type is
"motorized_10m".

Only mention vessel-specific suitability when the supplied Safety Assessment
contains an explicit vessel-specific assessment.

Even then, do not imply that weather data certifies a vessel as safe.

Vessel condition, equipment, crew, operating requirements, regulations,
and local conditions also matter.

6. GEOSPATIAL / LEGAL QUESTIONS

For geographic or legal questions, focus only on the supplied geospatial data.

Relevant information may include:

- Restricted areas
- Fishing bans
- Marine Protected Areas
- EEZ
- Geographic boundaries

Do not claim that the user's physical GPS location is known unless GPS/device
location is explicitly supplied.

If the system provides only a selected or queried location, describe it as:

"the selected location"

or

"the queried location"

and NOT as the user's physical current location.

When reporting EEZ status for a selected or queried location, say:

"The queried location is within India's 200 NM Exclusive Economic Zone (EEZ)."

Do not say that the user is currently within the EEZ unless explicit device or
GPS coordinates are supplied.

7. REAL-TIME DATA

Only provide numerical/current data that exists in the supplied specialist
data.

Never invent:

- Wind values
- Wave values
- SST
- Chlorophyll
- Coordinates
- Warnings
- PFZ locations
- Restrictions
- Safety assessments

8. SAFETY PRIORITY

If an explicitly supplied Safety Assessment reports DANGER, communicate the
warning clearly.

If it reports CAUTION, clearly communicate the caution.

Do not turn missing data into a claim that conditions are safe.

9. LANGUAGE

Respond in the same language as the user's question unless another language
is explicitly requested.

10. STYLE

- Be concise.
- Answer directly.
- Use short bullets when useful.
- Avoid unnecessary greetings.
- Avoid repetition.
- Do not output raw JSON.
- Do not output Python objects.
- Do not add generic filler.
- Do not make unsupported claims.

11. DATA PRIORITY

- Weather question -> Weather Agent
- PFZ/ocean question -> Ocean Agent
- Safety question -> Safety Agent
- Geographic/legal question -> Geospatial Agent
- Knowledge question -> Knowledge Agent

Never replace Ocean/PFZ data with Weather data.
Never replace Safety data with Weather data.
"""


def _to_dict(data: Any) -> Optional[dict]:
    """
    Convert Pydantic models, dictionaries, or simple objects into dictionaries.
    """
    if data is None:
        return None

    try:
        if hasattr(data, "model_dump"):
            return data.model_dump()

        if hasattr(data, "dict"):
            return data.dict()

        if isinstance(data, dict):
            return data

        if hasattr(data, "__dict__"):
            return vars(data)

    except Exception as exc:
        logger.warning(
            "Failed to convert agent data to dict: %s",
            exc,
        )

    return {"value": str(data)}


def _clean_response(response: Any) -> str:
    """
    Clean the LLM response.
    """
    if response is None:
        return ""

    if isinstance(response, dict):
        for key in ("text", "response", "answer", "content"):
            if key in response:
                return str(response[key]).strip()

        return json.dumps(
            response,
            ensure_ascii=False,
        )

    text = str(response).strip()

    # Remove accidental markdown code fences.
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()

        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    return text


def _get_value(data: Optional[dict], *keys: str) -> Any:
    """
    Return the first non-None value from a dictionary.
    """
    if not data:
        return None

    for key in keys:
        value = data.get(key)

        if value is not None:
            return value

    return None


def _format_pfz_response(
    query: str,
    ocean: dict,
    location: Optional[Any] = None,
) -> Optional[str]:
    """
    Deterministically format PFZ/ocean information when possible.

    This prevents the LLM from replacing Ocean Agent information with
    unrelated weather information.
    """

    if not ocean:
        return None

    score = _get_value(
        ocean,
        "pfz_suitability_score",
        "suitability_score",
    )

    classification = _get_value(
        ocean,
        "pfz_classification",
        "classification",
    )

    sst = _get_value(
        ocean,
        "sst_celsius",
        "sst",
    )

    chlorophyll = _get_value(
        ocean,
        "chlorophyll_mg_m3",
        "chlorophyll",
        "chlorophyll_mg_per_m3",
    )

    thermal_front = _get_value(
        ocean,
        "thermal_front_detected",
        "thermal_front",
    )

    pfz_coordinates = _get_value(
        ocean,
        "pfz_coordinates",
        "coordinates",
        "pfz_location",
    )

    bearing = _get_value(
        ocean,
        "pfz_bearing",
        "bearing",
    )

    distance = _get_value(
        ocean,
        "pfz_distance_km",
        "distance_km",
        "pfz_distance",
    )

    message = _get_value(
        ocean,
        "pfz_message",
        "message",
    )

    lines = []

    # Location information.
    if pfz_coordinates is not None:
        lines.append(f"PFZ location: {pfz_coordinates}")
    elif bearing is not None or distance is not None:
        location_parts = []

        if bearing is not None:
            location_parts.append(f"bearing {bearing}")

        if distance is not None:
            location_parts.append(f"distance {distance}")

        lines.append(
            "PFZ location: " + ", ".join(location_parts)
        )
    else:
        lines.append(
            "Specific PFZ coordinates, bearing, and distance are unavailable."
        )

    # PFZ score.
    if score is not None:
        try:
            numeric_score = float(score)

            # The schema uses 0.0 - 1.0.
            if 0.0 <= numeric_score <= 1.0:
                score_display = numeric_score * 100
            else:
                score_display = numeric_score

            score_line = f"PFZ suitability score: {score_display:.0f}/100"

            if classification:
                score_line += f" ({classification})"

            lines.append(score_line)

        except (TypeError, ValueError):
            lines.append(f"PFZ suitability score: {score}")

    elif classification:
        lines.append(f"PFZ classification: {classification}")

    # Ocean measurements.
    if sst is not None:
        try:
            lines.append(f"Sea surface temperature: {float(sst):.1f}°C")
        except (TypeError, ValueError):
            lines.append(f"Sea surface temperature: {sst}")

    if chlorophyll is not None:
        try:
            lines.append(
                f"Chlorophyll: {float(chlorophyll):.2f} mg/m³"
            )
        except (TypeError, ValueError):
            lines.append(f"Chlorophyll: {chlorophyll}")

    if thermal_front is not None:
        if isinstance(thermal_front, bool):
            thermal_text = (
                "detected"
                if thermal_front
                else "not detected"
            )
            lines.append(f"Thermal front: {thermal_text}")
        else:
            lines.append(
                f"Thermal front: {thermal_front}"
            )

    if message:
        lines.append(str(message))

    # Always qualify PFZ information.
    lines.append(
        "PFZ information is a scientific advisory and is not a guarantee "
        "of fish availability."
    )

    # Only return a deterministic answer if we actually have useful
    # Ocean Agent information.
    useful_fields = any(
        value is not None
        for value in (
            score,
            classification,
            sst,
            chlorophyll,
            thermal_front,
            pfz_coordinates,
            bearing,
            distance,
            message,
        )
    )

    if not useful_fields:
        return None

    return "\n".join(lines)


def explainer_agent(
    query: str,
    weather_data: Optional[Any] = None,
    ocean_data: Optional[Any] = None,
    geo_data: Optional[Any] = None,
    safety_data: Optional[Any] = None,
    knowledge_data: Optional[Any] = None,
    intent: Optional[str] = None,
    location: Optional[Any] = None,
    date: Optional[Any] = None,
) -> dict:
    """
    Final response-generation agent.

    Specialist agents provide factual data.

    Python deterministically selects the specialist data relevant to the
    planner intent before the LLM is called.
    """

    try:
        # ---------------------------------------------------------
        # Normalize intent
        # ---------------------------------------------------------

        intent_upper = str(intent or "").upper().strip()

        intent_upper = (
            intent_upper
            .replace("-", "_")
            .replace(" ", "_")
        )

        logger.debug(
            "Explainer received intent=%s",
            intent_upper,
        )

        # ---------------------------------------------------------
        # Convert specialist outputs
        # ---------------------------------------------------------

        weather = _to_dict(weather_data)
        ocean = _to_dict(ocean_data)
        geo = _to_dict(geo_data)
        safety = _to_dict(safety_data)
        knowledge = _to_dict(knowledge_data)

        # ---------------------------------------------------------
        # Select relevant specialist data
        # ---------------------------------------------------------

        relevant_data = {}

        # ---------------------------------------------------------
        # WEATHER
        # ---------------------------------------------------------

        weather_intents = {
            "WEATHER_QUERY",
            "WEATHER",
            "FORECAST",
            "WEATHER_FORECAST",
            "WIND_QUERY",
            "WAVE_QUERY",
        }

        if (
            intent_upper in weather_intents
            or "WEATHER" in intent_upper
            or "FORECAST" in intent_upper
        ):
            if weather is not None:
                relevant_data["weather"] = weather

        # ---------------------------------------------------------
        # PFZ / OCEAN / FISHING
        # ---------------------------------------------------------

        elif (
            intent_upper in {
                "PFZ_QUERY",
                "PFZ",
                "OCEAN_QUERY",
                "OCEAN",
                "FISHING_QUERY",
                "FISHING_ZONE_QUERY",
                "FISHING_ZONES_QUERY",
                "FISHING_ZONE",
                "FISHING_ZONES",
                "SEA_CONDITION_QUERY",
                "SEA_CONDITIONS",
                "FISHING_LOCATION_QUERY",
            }
            or "PFZ" in intent_upper
            or "OCEAN" in intent_upper
            or "FISHING_ZONE" in intent_upper
            or "FISHING_ZONES" in intent_upper
        ):
            # Ocean MUST be the primary source.
            if ocean is not None:
                relevant_data["ocean"] = ocean

            # Do NOT automatically add weather or safety here.

            # Only include safety if the intent explicitly contains
            # safety/hazard terminology.
            if safety is not None and (
                "SAFETY" in intent_upper
                or "SAFE" in intent_upper
                or "HAZARD" in intent_upper
            ):
                relevant_data["safety"] = safety

        # ---------------------------------------------------------
        # SAFETY
        # ---------------------------------------------------------

        elif (
            intent_upper in {
                "SAFETY_CHECK",
                "SAFETY_QUERY",
                "SAFETY",
                "HAZARD_QUERY",
                "RISK_QUERY",
            }
            or "SAFETY" in intent_upper
            or "HAZARD" in intent_upper
            or "RISK" in intent_upper
        ):
            if safety is not None:
                relevant_data["safety"] = safety

            if weather is not None:
                relevant_data["weather"] = weather

            if ocean is not None:
                relevant_data["ocean"] = ocean

            if geo is not None:
                relevant_data["geospatial"] = geo

        # ---------------------------------------------------------
        # GEOSPATIAL / RESTRICTIONS
        # ---------------------------------------------------------

        elif (
            intent_upper in {
                "BOUNDARY_QUERY",
                "BOUNDARY_CHECK",
                "GEO_QUERY",
                "GEOSPATIAL_QUERY",
                "GEOSPATIAL",
                "RESTRICTION_QUERY",
                "RESTRICTIONS_QUERY",
                "RESTRICTED_AREA_QUERY",
                "FISHING_BAN_QUERY",
                "MPA_QUERY",
                "EEZ_QUERY",
            }
            or "BOUNDARY" in intent_upper
            or "GEOSPATIAL" in intent_upper
            or "RESTRICT" in intent_upper
            or "BAN" in intent_upper
            or "MPA" in intent_upper
            or "EEZ" in intent_upper
        ):
            if geo is not None:
                relevant_data["geospatial"] = geo

        # ---------------------------------------------------------
        # KNOWLEDGE
        # ---------------------------------------------------------

        elif (
            intent_upper in {
                "KNOWLEDGE_QUERY",
                "KNOWLEDGE",
                "GENERAL_INFO",
                "GENERAL_QUERY",
                "INFORMATION_QUERY",
            }
            or "KNOWLEDGE" in intent_upper
            or "GENERAL_INFO" in intent_upper
        ):
            if knowledge is not None:
                relevant_data["knowledge"] = knowledge

        # ---------------------------------------------------------
        # UNKNOWN INTENT
        # ---------------------------------------------------------

        else:
            query_upper = str(query or "").upper()

            # PFZ / fishing zone has priority.
            if (
                "PFZ" in query_upper
                or "POTENTIAL FISHING ZONE" in query_upper
                or "POTENTIAL FISHING ZONES" in query_upper
                or "FISHING ZONE" in query_upper
                or "FISHING ZONES" in query_upper
                or "FISHING AREA" in query_upper
                or "FISHING LOCATION" in query_upper
            ):
                if ocean is not None:
                    relevant_data["ocean"] = ocean

            # Geospatial/legal.
            elif (
                "RESTRICTED" in query_upper
                or "FISHING BAN" in query_upper
                or "FISHING BANS" in query_upper
                or "MARINE PROTECTED" in query_upper
                or "MPA" in query_upper
                or "EEZ" in query_upper
                or "BOUNDARY" in query_upper
            ):
                if geo is not None:
                    relevant_data["geospatial"] = geo

            # Safety.
            elif (
                "SAFE" in query_upper
                or "SAFETY" in query_upper
                or "HAZARD" in query_upper
                or "DANGER" in query_upper
                or "RISK" in query_upper
            ):
                if safety is not None:
                    relevant_data["safety"] = safety

                if weather is not None:
                    relevant_data["weather"] = weather

            # Weather.
            elif (
                "WEATHER" in query_upper
                or "WIND" in query_upper
                or "WAVE" in query_upper
                or "FORECAST" in query_upper
            ):
                if weather is not None:
                    relevant_data["weather"] = weather

            # Ocean fallback.
            elif ocean is not None:
                relevant_data["ocean"] = ocean

            elif weather is not None:
                relevant_data["weather"] = weather

            elif safety is not None:
                relevant_data["safety"] = safety

            elif geo is not None:
                relevant_data["geospatial"] = geo

            elif knowledge is not None:
                relevant_data["knowledge"] = knowledge

        # ---------------------------------------------------------
        # No relevant data
        # ---------------------------------------------------------

        if not relevant_data:
            return {
                "text": (
                    "I don't have the required current data to answer "
                    "that question accurately."
                ),
                "confidence": 0.0,
            }

        logger.debug(
            "Explainer selected data sources: %s",
            list(relevant_data.keys()),
        )

        # ---------------------------------------------------------
        # IMPORTANT:
        # Deterministic PFZ response
        #
        # This prevents Groq from accidentally turning a PFZ query
        # into a weather/safety response.
        # ---------------------------------------------------------

        if "ocean" in relevant_data and (
            intent_upper in {
                "PFZ_QUERY",
                "PFZ",
                "FISHING_ZONE_QUERY",
                "FISHING_ZONES_QUERY",
                "FISHING_ZONE",
                "FISHING_ZONES",
                "FISHING_LOCATION_QUERY",
            }
            or "PFZ" in str(query or "").upper()
            or "POTENTIAL FISHING ZONE" in str(query or "").upper()
            or "POTENTIAL FISHING ZONES" in str(query or "").upper()
        ):
            deterministic_response = _format_pfz_response(
                query=query,
                ocean=relevant_data["ocean"],
                location=location,
            )

            if deterministic_response:
                return {
                    "text": deterministic_response,
                    "confidence": 0.95,
                }

        # ---------------------------------------------------------
        # Build structured context for LLM
        # ---------------------------------------------------------

        context = {
            "query": query,
            "intent": intent_upper or None,
            "location": location,
            "date": date,
            "data": relevant_data,
        }

        context_json = json.dumps(
            context,
            ensure_ascii=False,
            default=str,
            indent=2,
        )

        # ---------------------------------------------------------
        # Final prompt
        # ---------------------------------------------------------

        prompt = f"""
{EXPLAINER_PROMPT}

USER QUESTION:
{query}

PLANNER INTENT:
{intent_upper or "UNKNOWN"}

LOCATION:
{location if location is not None else "Not specified"}

DATE:
{date if date is not None else "Not specified"}

SPECIALIST DATA:
{context_json}

FINAL RESPONSE REQUIREMENTS:

1. Answer the user's exact question.

2. Use ONLY the specialist data supplied above.

3. Do not invent missing values.

4. For PFZ/ocean questions, use ONLY Ocean Agent data.

5. For weather questions, use Weather Agent data.

6. For safety questions, use Safety Agent data.

7. For geographic/legal questions, use Geospatial Agent data.

8. Do not replace PFZ/ocean information with weather information.

9. Do not infer vessel-size suitability.

10. Do not claim the user is physically at a location unless GPS/device
location is explicitly supplied.

11. If PFZ coordinates, bearing, or distance are missing, say so explicitly.

12. If a PFZ classification is supplied, report that classification.

13. If only a numerical PFZ score is supplied, report the numerical score
without inventing a qualitative interpretation.

14. Mention that PFZ information is a scientific advisory and not a guarantee
of fish availability.

15. Do not include unrelated specialist information.

16. Keep the answer concise.

Now answer the user.
"""

        logger.debug(
            "Calling Explainer LLM with intent=%s and data=%s",
            intent_upper,
            list(relevant_data.keys()),
        )

        # ---------------------------------------------------------
        # Call Groq
        # ---------------------------------------------------------

        api_key = os.getenv("GROQ_API_KEY", "")
        response = (
            _call_groq_api(api_key, prompt)
            if api_key
            else None
        )

        text = _clean_response(response)

        if "geospatial" in relevant_data and text:
            text = re.sub(
                r"(?:\*\*)?(?:EEZ Status|You are currently within)(?::)?(?:\*\*)?:?\s*"
                r"(?:Within |The location is within |You are currently within )?India's 200 NM Exclusive Economic Zone \(EEZ\)\.?",
                "The queried location is within India's 200 NM Exclusive Economic Zone (EEZ).",
                text,
                flags=re.IGNORECASE,
            )

        # ---------------------------------------------------------
        # Empty response protection
        # ---------------------------------------------------------

        if not text:
            return {
                "text": (
                    "I could not generate a response from the available "
                    "marine data."
                ),
                "confidence": 0.0,
            }

        # ---------------------------------------------------------
        # Return
        # ---------------------------------------------------------

        return {
            "text": text,
            "confidence": 0.9,
        }

    except Exception as exc:
        logger.exception(
            "Explainer agent failed: %s",
            exc,
        )

        return {
            "text": (
                "I couldn't process the available marine information "
                "right now."
            ),
            "confidence": 0.0,
            "error": str(exc),
        }
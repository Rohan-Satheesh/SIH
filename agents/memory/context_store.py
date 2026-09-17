import re
from typing import Dict, Tuple, Optional, Any

PORTS_AND_COORDINATES: Dict[str, Tuple[float, float, str]] = {
    "kochi": (9.93, 75.82, "Kochi Sector K-04"),
    "cochin": (9.93, 75.82, "Kochi Sector K-04"),
    "കൊച്ചി": (9.93, 75.82, "Kochi Sector K-04"),
    "munambam": (10.20, 75.80, "Munambam Sector M-02"),
    "മുനമ്പം": (10.20, 75.80, "Munambam Sector M-02"),
    "alappuzha": (9.45, 76.15, "Alappuzha Shoals A-09"),
    "ആലപ്പുഴ": (9.45, 76.15, "Alappuzha Shoals A-09"),
    "goa": (15.35, 73.55, "Goa Coastal Zone G-08"),
    "mumbai": (18.90, 72.40, "Mumbai High Marine Corridor B-12"),
    "mangalore": (12.82, 74.52, "Mangalore Deep Sector MN-03"),
    "chennai": (13.10, 80.45, "Chennai Coromandel Sector C-03"),
    "vizag": (17.65, 83.42, "Visakhapatnam Shelf V-06"),
    "visakhapatnam": (17.65, 83.42, "Visakhapatnam Shelf V-06"),
    "rameswaram": (9.25, 79.35, "Palk Strait / Rameswaram R-01"),
    "kutch": (22.40, 69.20, "Gulf of Kutch GK-05"),
    "gulf of kutch": (22.40, 69.20, "Gulf of Kutch GK-05"),
    "gujarat": (22.40, 69.20, "Gulf of Kutch GK-05"),
    "odisha": (20.20, 86.68, "Paradip Coastal Sector P-02"),
    "paradip": (20.20, 86.68, "Paradip Coastal Sector P-02"),
    "bengal": (21.50, 88.50, "Sundarbans Marine Sector SB-01"),
    "sundarbans": (21.50, 88.50, "Sundarbans Marine Sector SB-01"),
    "kollam": (8.89, 76.55, "Kollam Bight Sector KL-07"),
    "kozhikode": (11.25, 75.77, "Kozhikode Malabar Sector MZ-01"),
    "trivandrum": (8.48, 76.92, "Vizhinjam Deep Horizon VZ-01"),
    "veraval": (20.90, 70.36, "Veraval Saurashtra Sector SV-02"),
    "porbandar": (21.64, 69.60, "Porbandar Marine Corridor PB-01")
}

def extract_target_location(
    query: str, 
    session: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None
) -> Tuple[float, float, str]:
    """
    Extracts coordinates or coastal sector:
    1. Direct coordinate match in user query (e.g. "9.93, 75.82")
    2. Explicit port/sector named in user query (e.g. "wave conditions near Mumbai")
    3. Active location selected by user in UI context (e.g. context["coordinates"] or context["location"])
    4. Session memory from prior turns
    5. Default fallback to Kochi Sector K-04
    """
    q = query.lower()

    # 1. Coordinate match e.g. "9.93, 75.82" in query text
    coord_match = re.search(r'([0-9]+\.?[0-9]*)\s*[°\s]*[nN]?\s*,\s*([0-9]+\.?[0-9]*)\s*[°\s]*[eE]?', query)
    if coord_match:
        try:
            lat = float(coord_match.group(1))
            lon = float(coord_match.group(2))
            loc = (lat, lon, f"Coordinates ({lat:.2f}°N, {lon:.2f}°E)")
            if session is not None:
                session["last_location"] = loc
            return loc
        except ValueError:
            pass

    # 2. Match coastal port names mentioned in query text
    for key, (lat, lon, name) in PORTS_AND_COORDINATES.items():
        if key in q or key in query:
            loc = (lat, lon, name)
            if session is not None:
                session["last_location"] = loc
            return loc

    # 3. Use active Location / Coordinates from frontend request context
    if context and isinstance(context, dict):
        coords = context.get("coordinates")
        if isinstance(coords, dict):
            lat = coords.get("lat") or coords.get("latitude")
            lon = coords.get("lon") or coords.get("lng") or coords.get("longitude")
            if lat is not None and lon is not None:
                loc_name = context.get("location") or f"Sector ({float(lat):.2f}°N, {float(lon):.2f}°E)"
                loc = (float(lat), float(lon), str(loc_name))
                if session is not None:
                    session["last_location"] = loc
                return loc

        loc_name = context.get("location")
        if loc_name and isinstance(loc_name, str):
            loc_key = loc_name.lower().strip()
            for key, (lat, lon, name) in PORTS_AND_COORDINATES.items():
                if key in loc_key:
                    loc = (lat, lon, loc_name)
                    if session is not None:
                        session["last_location"] = loc
                    return loc

    # 4. Contextual session memory
    if session and session.get("last_location"):
        return session["last_location"]

    # 5. Default fallback
    return (9.93, 75.82, "Kochi Sector K-04")

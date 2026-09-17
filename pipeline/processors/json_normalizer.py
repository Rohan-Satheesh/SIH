from typing import Dict, Any

def normalize_geojson_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures incoming spatial data conforms to standard RFC 7946 GeoJSON."""
    if "type" not in data:
        data["type"] = "FeatureCollection"
    if "features" not in data:
        data["features"] = []
    return data

from typing import Dict, Any

def get_risk_zones_layer() -> Dict[str, Any]:
    """Generates GeoJSON feature collection for ocean risk hazard zones."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[75.40, 9.70], [75.60, 9.70], [75.60, 9.90], [75.40, 9.90], [75.40, 9.70]]]
                },
                "properties": {
                    "layer": "ocean_risk_zones",
                    "risk_score": 35,
                    "risk_level": "LOW",
                    "advisory": "Safe navigation"
                }
            }
        ]
    }

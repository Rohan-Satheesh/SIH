from typing import Dict, Any

def get_sst_thermal_fronts() -> Dict[str, Any]:
    """Generates GeoJSON feature collection for Sea Surface Temperature thermal boundaries."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[75.60, 9.85], [75.75, 9.95], [75.90, 10.15]]
                },
                "properties": {
                    "layer": "sst_thermal_fronts",
                    "temperature_gradient": "0.8°C/km",
                    "sst_c": 28.4,
                    "upwelling_confidence": "HIGH"
                }
            }
        ]
    }

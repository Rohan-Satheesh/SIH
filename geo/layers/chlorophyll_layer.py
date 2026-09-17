from typing import Dict, Any

def get_chlorophyll_bloom_features() -> Dict[str, Any]:
    """Generates GeoJSON feature collection for chlorophyll concentration blooms."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[75.68, 9.90], [75.76, 9.90], [75.76, 9.98], [75.68, 9.98], [75.68, 9.90]]]
                },
                "properties": {
                    "layer": "chlorophyll_blooms",
                    "concentration_mg_m3": 1.6,
                    "productivity_rating": "OPTIMAL",
                    "sensor": "Oceansat-3 OCM-3"
                }
            }
        ]
    }

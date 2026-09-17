from typing import Dict, Any, List, Optional
import math
from geo.services.spatial_cache import (
    get_all_available_layers as cache_get_all_layers,
    get_optimized_geojson,
    load_local_geodataframe
)

def get_all_available_layers(engine=None) -> Dict[str, Any]:
    """Returns metadata for all available geospatial layers."""
    cached = cache_get_all_layers(engine)
    layers_dict = {}
    for name, gdf in cached.items():
        layers_dict[name] = {
            "layer_name": name,
            "display_name": name.replace("_", " ").title(),
            "geometry_type": "MultiPolygon" if not gdf.empty else "Geometry",
            "feature_count": len(gdf)
        }
    return layers_dict

def get_geojson_layer(engine, layer_name: str, simplify: float = 0.005) -> Optional[Dict[str, Any]]:
    """Returns optimized GeoJSON for a given layer name."""
    data = get_optimized_geojson(layer_name, tolerance=simplify)
    if data:
        return data
        
    if layer_name == "sst_thermal_fronts":
        from geo.layers.sst_layer import get_sst_thermal_fronts
        return get_sst_thermal_fronts()
    elif layer_name == "chlorophyll_blooms":
        from geo.layers.chlorophyll_layer import get_chlorophyll_bloom_features
        return get_chlorophyll_bloom_features()
    elif layer_name == "ocean_risk_zones":
        from geo.layers.risk_layer import get_risk_zones_layer
        return get_risk_zones_layer()
    elif layer_name == "composite_risk_grid":
        from geo.analysis.risk_calculator import generate_composite_risk_grid
        return generate_composite_risk_grid()
        
    return None

def generate_ocean_layers(layer_type: str = "sst") -> Dict[str, Any]:
    """
    Generates dynamic, spatially continuous GeoJSON contour bands for:
    - Sea Surface Temperature (SST) frontal boundaries.
    - Chlorophyll-a concentration zones.
    """
    if layer_type == "chlorophyll":
        from geo.layers.chlorophyll_layer import get_chlorophyll_bloom_features
        return get_chlorophyll_bloom_features()
    from geo.layers.sst_layer import get_sst_thermal_fronts
    return get_sst_thermal_fronts()

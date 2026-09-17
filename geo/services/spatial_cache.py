import os
import glob
import json
from typing import Dict, Any, Optional
import geopandas as gpd

BOUNDARIES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "boundaries"))
LEGACY_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "data"))

_GDF_CACHE: Dict[str, gpd.GeoDataFrame] = {}
_SIMPLIFIED_GEOJSON_CACHE: Dict[str, Dict[str, Any]] = {}

def _get_search_dirs():
    dirs = []
    if os.path.exists(BOUNDARIES_DIR):
        dirs.append(BOUNDARIES_DIR)
    if os.path.exists(LEGACY_DATA_DIR):
        dirs.append(LEGACY_DATA_DIR)
    return dirs

def load_local_geodataframe(layer_name: str) -> Optional[gpd.GeoDataFrame]:
    if layer_name in _GDF_CACHE:
        return _GDF_CACHE[layer_name]

    for d in _get_search_dirs():
        target_files = [
            os.path.join(d, f"{layer_name}.geojson"),
            os.path.join(d, f"{layer_name}.json"),
        ]
        for fp in target_files:
            if os.path.exists(fp):
                try:
                    gdf = gpd.read_file(fp)
                    if gdf.crs is None:
                        gdf.set_crs("EPSG:4326", inplace=True)
                    elif gdf.crs != "EPSG:4326":
                        gdf = gdf.to_crs("EPSG:4326")
                    _GDF_CACHE[layer_name] = gdf
                    return gdf
                except Exception as e:
                    print(f"Error loading {fp}: {e}")

        for fp in glob.glob(os.path.join(d, "*.geojson")):
            base = os.path.splitext(os.path.basename(fp))[0]
            if base == layer_name or layer_name in base:
                try:
                    gdf = gpd.read_file(fp)
                    if gdf.crs is None:
                        gdf.set_crs("EPSG:4326", inplace=True)
                    _GDF_CACHE[layer_name] = gdf
                    return gdf
                except Exception as e:
                    print(f"Error loading {fp}: {e}")

    return None

def get_all_available_layers(engine=None) -> Dict[str, Any]:
    for d in _get_search_dirs():
        for fp in glob.glob(os.path.join(d, "*.geojson")):
            layer_name = os.path.splitext(os.path.basename(fp))[0]
            if layer_name not in _GDF_CACHE:
                load_local_geodataframe(layer_name)
    return _GDF_CACHE

def get_optimized_geojson(layer_name: str, tolerance: float = 0.005) -> Optional[Dict[str, Any]]:
    cache_key = f"{layer_name}_tol_{tolerance}"
    if cache_key in _SIMPLIFIED_GEOJSON_CACHE:
        return _SIMPLIFIED_GEOJSON_CACHE[cache_key]

    gdf = load_local_geodataframe(layer_name)
    if gdf is None or gdf.empty:
        return None

    try:
        simplified_gdf = gdf.copy()
        if tolerance > 0:
            simplified_gdf["geometry"] = simplified_gdf["geometry"].simplify(
                tolerance=tolerance, 
                preserve_topology=True
            )
        geojson_dict = json.loads(simplified_gdf.to_json())
        _SIMPLIFIED_GEOJSON_CACHE[cache_key] = geojson_dict
        return geojson_dict
    except Exception as e:
        print(f"Error simplifying {layer_name}: {e}")
        return json.loads(gdf.to_json())

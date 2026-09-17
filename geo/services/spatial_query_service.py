"""
NeerMitra Geospatial Intelligence Engine - Spatial Bounding Box & Polygon Query Service
Implements Task 8 of the Geospatial & Map Services Roadmap.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy import text
from sqlalchemy.engine import Engine
from shapely.geometry import box

from geo.services.spatial_cache import load_local_geodataframe
from geo.analysis.pfz_analyzer import INDIAN_PFZ_HOTSPOTS

def query_bounding_box_features(
    engine: Optional[Engine], 
    min_lat: float, 
    min_lon: float, 
    max_lat: float, 
    max_lon: float
) -> Dict[str, Any]:
    """
    Finds all spatial entities (MPAs, EEZ intersections, coastal fishing sectors, PFZs)
    that intersect a given geographic bounding box.
    """
    bbox_geom = box(min_lon, min_lat, max_lon, max_lat)
    
    result: Dict[str, Any] = {
        "bbox": {"min_lat": min_lat, "min_lon": min_lon, "max_lat": max_lat, "max_lon": max_lon},
        "intersecting_mpas": [],
        "intersecting_sectors": [],
        "intersecting_pfzs": [],
        "feature_count": 0,
        "geojson": {
            "type": "FeatureCollection",
            "features": []
        }
    }

    # 1. MPAs
    mpa_gdf = load_local_geodataframe("india_marine_protected_areas")
    if mpa_gdf is not None and not mpa_gdf.empty:
        matches = mpa_gdf[mpa_gdf.intersects(bbox_geom)]
        for _, row in matches.iterrows():
            m_dict = {
                "name": row.get("name", "MPA"),
                "category": row.get("category", "Sanctuary"),
                "state": row.get("state", "India"),
                "restrictions": row.get("protection_level", row.get("restrictions", "Restricted"))
            }
            result["intersecting_mpas"].append(m_dict)

    # 2. Sectors
    sector_gdf = load_local_geodataframe("india_coastal_fishing_sectors")
    if sector_gdf is not None and not sector_gdf.empty:
        matches = sector_gdf[sector_gdf.intersects(bbox_geom)]
        for _, row in matches.iterrows():
            s_dict = {
                "sector_name": row.get("name", row.get("sector_name", "Fishing Sector")),
                "state": row.get("coastal_state", row.get("state", "India")),
                "depth_range": row.get("depth_range_m", row.get("authorized_depth_range", "0-50m")),
                "target_species": row.get("primary_catch", row.get("target_species", "Pelagic / Demersal"))
            }
            result["intersecting_sectors"].append(s_dict)

    # 3. PFZs in BBOX
    for p in INDIAN_PFZ_HOTSPOTS:
        if min_lat <= p["lat"] <= max_lat and min_lon <= p["lon"] <= max_lon:
            result["intersecting_pfzs"].append(p)
            result["geojson"]["features"].append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [p["lon"], p["lat"]]
                },
                "properties": {
                    "id": p["id"],
                    "name": p["name"],
                    "sst": f"{p['sst_c']}°C",
                    "species": p["species"]
                }
            })

    result["feature_count"] = len(result["intersecting_mpas"]) + len(result["intersecting_sectors"]) + len(result["intersecting_pfzs"])
    return result

query_layers_by_bbox = query_bounding_box_features

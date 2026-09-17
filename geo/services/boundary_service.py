"""
NeerMitra Geospatial Intelligence Engine - Boundary & Geofence Service
Implements Task 2 (Boundary Check) & Task 3 (Geofence Monitoring) of the Geospatial & Map Services Roadmap.
"""

from typing import Dict, Any, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.engine import Engine
from shapely.geometry import Point
import math

from .spatial_cache import load_local_geodataframe

def calculate_initial_compass_bearing(point_a: Tuple[float, float], point_b: Tuple[float, float]) -> float:
    """
    Calculates the initial bearing in degrees from point A (lat1, lon1) to point B (lat2, lon2).
    """
    lat1 = math.radians(point_a[0])
    lat2 = math.radians(point_b[0])
    diff_long = math.radians(point_b[1] - point_a[1])

    x = math.sin(diff_long) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diff_long))

    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return round(compass_bearing, 1)

def get_compass_direction_name(bearing: float) -> str:
    directions = [
        "NORTH", "NORTH-NORTHEAST", "NORTHEAST", "EAST-NORTHEAST",
        "EAST", "EAST-SOUTHEAST", "SOUTHEAST", "SOUTH-SOUTHEAST",
        "SOUTH", "SOUTH-SOUTHWEST", "SOUTHWEST", "WEST-SOUTHWEST",
        "WEST", "WEST-NORTHWEST", "NORTHWEST", "NORTH-NORTHWEST"
    ]
    idx = int((bearing + 11.25) / 22.5) % 16
    return directions[idx]

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates great-circle distance between two points in kilometers.
    """
    R = 6371.0 # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def _check_boundaries_postgis(engine: Engine, lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Executes native PostGIS spatial queries against postgres tables.
    """
    try:
        with engine.connect() as conn:
            # 1. EEZ Check
            eez_query = text("""
                SELECT 
                    geoname,
                    ST_Contains(geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) AS is_inside
                FROM "india_eez_boundaries"
                ORDER BY is_inside DESC
                LIMIT 1;
            """)
            eez_res = conn.execute(eez_query, {"lat": lat, "lon": lon}).fetchone()
            
            is_inside_eez = bool(eez_res and eez_res[1])
            eez_name = eez_res[0] if eez_res else "Indian Exclusive Economic Zone"
            dist_eez_km = 0.0
            dist_eez_nm = 0.0

            if not is_inside_eez:
                dist_eez_query = text("""
                    SELECT ST_Distance(geometry::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS dist_meters
                    FROM "india_eez_boundaries"
                    ORDER BY dist_meters ASC
                    LIMIT 1;
                """)
                dist_res = conn.execute(dist_eez_query, {"lat": lat, "lon": lon}).fetchone()
                if dist_res and dist_res[0] is not None:
                    dist_eez_km = round(dist_res[0] / 1000.0, 2)
                    dist_eez_nm = round(dist_res[0] / 1852.0, 2)

            # 2. MPA Check
            mpa_query = text("""
                SELECT 
                    name, category, state, restrictions,
                    ST_Contains(geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) AS is_inside,
                    ST_Distance(geometry::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS dist_meters
                FROM "india_marine_protected_areas"
                ORDER BY is_inside DESC, dist_meters ASC
                LIMIT 1;
            """)
            mpa_res = conn.execute(mpa_query, {"lat": lat, "lon": lon}).fetchone()

            is_inside_mpa = False
            mpa_details = None
            nearest_mpa = None

            if mpa_res:
                is_inside_mpa = bool(mpa_res[4])
                dist_mpa_km = round(mpa_res[5] / 1000.0, 2) if mpa_res[5] is not None else 0.0
                dist_mpa_nm = round(mpa_res[5] / 1852.0, 2) if mpa_res[5] is not None else 0.0
                nearest_mpa = {
                    "name": mpa_res[0],
                    "category": mpa_res[1],
                    "state": mpa_res[2],
                    "restrictions": mpa_res[3],
                    "distance_km": dist_mpa_km,
                    "distance_nm": dist_mpa_nm
                }
                if is_inside_mpa:
                    mpa_details = nearest_mpa

            # 3. Sector Check
            sector_query = text("""
                SELECT sector_name, state, authorized_depth_range, monsoon_trawl_ban_period, target_species
                FROM "india_coastal_fishing_sectors"
                WHERE ST_Contains(geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) = true
                LIMIT 1;
            """)
            sector_res = conn.execute(sector_query, {"lat": lat, "lon": lon}).fetchone()
            coastal_sector = None
            if sector_res:
                coastal_sector = {
                    "sector_name": sector_res[0],
                    "state": sector_res[1],
                    "depth_range": sector_res[2],
                    "monsoon_ban": sector_res[3],
                    "target_species": sector_res[4]
                }

            # Determine Geofence Status
            if is_inside_mpa:
                geofence_status = "MPA_BREACH"
                advisory = f"CRITICAL: Vessel is inside {nearest_mpa['name']}. Commercial fishing and trawling are prohibited."
            elif not is_inside_eez:
                geofence_status = "BORDER_WARNING"
                advisory = f"WARNING: Vessel has exited Indian EEZ by {dist_eez_nm} NM ({dist_eez_km} km)."
            elif nearest_mpa and nearest_mpa["distance_km"] < 10.0:
                geofence_status = "MPA_PROXIMITY_ALERT"
                advisory = f"CAUTION: Vessel is {nearest_mpa['distance_km']} km ({nearest_mpa['distance_nm']} NM) from {nearest_mpa['name']}."
            else:
                geofence_status = "SAFE"
                advisory = "Nominal operational status within authorized domestic waters."

            return {
                "coordinates": {"lat": lat, "lon": lon},
                "is_inside_eez": is_inside_eez,
                "eez_name": eez_name if is_inside_eez else None,
                "distance_to_eez_border_km": dist_eez_km,
                "distance_to_eez_border_nm": dist_eez_nm,
                "is_inside_mpa": is_inside_mpa,
                "mpa_details": mpa_details,
                "nearest_mpa": nearest_mpa,
                "coastal_sector": coastal_sector,
                "geofence_status": geofence_status,
                "advisory_message": advisory,
                "engine": "PostGIS v3.4 (PostgreSQL 15)"
            }
    except Exception:
        return None

def _check_boundaries_geopandas(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fallback using high-speed in-memory GeoPandas / Shapely R-Tree spatial indexing.
    """
    p = Point(lon, lat)
    
    # 1. EEZ
    eez_gdf = load_local_geodataframe("india_eez_boundaries")
    is_inside_eez = False
    eez_name = None
    dist_eez_km = 0.0
    dist_eez_nm = 0.0

    if eez_gdf is not None and not eez_gdf.empty:
        matches = eez_gdf[eez_gdf.contains(p)]
        if not matches.empty:
            is_inside_eez = True
            eez_name = matches.iloc[0].get("geoname", "Indian Exclusive Economic Zone")
        else:
            # Estimate distance to nearest boundary centroid/exterior
            min_d_deg = eez_gdf.distance(p).min()
            dist_eez_km = round(min_d_deg * 111.0, 2)
            dist_eez_nm = round(dist_eez_km / 1.852, 2)

    # 2. MPAs
    mpa_gdf = load_local_geodataframe("india_marine_protected_areas")
    is_inside_mpa = False
    mpa_details = None
    nearest_mpa = None

    if mpa_gdf is not None and not mpa_gdf.empty:
        inside_mpas = mpa_gdf[mpa_gdf.contains(p)]
        if not inside_mpas.empty:
            is_inside_mpa = True
            row = inside_mpas.iloc[0]
            mpa_details = {
                "name": row.get("name", "Marine Protected Area"),
                "category": row.get("category", "Sanctuary"),
                "state": row.get("state", "India"),
                "restrictions": row.get("protection_level", row.get("restrictions", "No Trawling")),
                "distance_km": 0.0,
                "distance_nm": 0.0
            }
            nearest_mpa = mpa_details
        else:
            # Calculate distance to all MPAs
            min_dist_km = 999999.0
            closest_row = None
            for _, r in mpa_gdf.iterrows():
                centroid = r.geometry.centroid
                d = haversine_distance(lat, lon, centroid.y, centroid.x)
                if d < min_dist_km:
                    min_dist_km = d
                    closest_row = r

            if closest_row is not None:
                nearest_mpa = {
                    "name": closest_row.get("name", "Marine Protected Area"),
                    "category": closest_row.get("category", "Sanctuary"),
                    "state": closest_row.get("state", "India"),
                    "restrictions": closest_row.get("protection_level", closest_row.get("restrictions", "No Trawling")),
                    "distance_km": round(min_dist_km, 2),
                    "distance_nm": round(min_dist_km / 1.852, 2)
                }

    # 3. Sectors
    sectors_gdf = load_local_geodataframe("india_coastal_fishing_sectors")
    coastal_sector = None
    if sectors_gdf is not None and not sectors_gdf.empty:
        matching_sectors = sectors_gdf[sectors_gdf.contains(p)]
        if not matching_sectors.empty:
            s_row = matching_sectors.iloc[0]
            coastal_sector = {
                "sector_name": s_row.get("name", s_row.get("sector_name", "Coastal Sector")),
                "state": s_row.get("coastal_state", s_row.get("state", "India")),
                "depth_range": s_row.get("depth_range_m", s_row.get("authorized_depth_range", "0-50m")),
                "monsoon_ban": s_row.get("trawling_regulation", s_row.get("monsoon_trawl_ban_period", "Active During Monsoon")),
                "target_species": s_row.get("primary_catch", s_row.get("target_species", "Pelagic / Demersal"))
            }

    # Geofence Status
    if is_inside_mpa:
        geofence_status = "MPA_BREACH"
        advisory = f"CRITICAL: Vessel is inside {nearest_mpa['name']}. Commercial fishing and trawling are strictly prohibited."
    elif not is_inside_eez and (lat < 5.0 or lat > 24.0 or lon < 65.0 or lon > 95.0 or dist_eez_km > 5.0):
        geofence_status = "BORDER_WARNING"
        advisory = f"WARNING: Vessel has exited Indian EEZ by {dist_eez_nm} NM ({dist_eez_km} km)."
    elif nearest_mpa and nearest_mpa["distance_km"] < 10.0:
        geofence_status = "MPA_PROXIMITY_ALERT"
        advisory = f"CAUTION: Vessel is {nearest_mpa['distance_km']} km ({nearest_mpa['distance_nm']} NM) from {nearest_mpa['name']}."
    else:
        geofence_status = "SAFE"
        advisory = "Nominal operational status within authorized domestic waters."

    return {
        "coordinates": {"lat": lat, "lon": lon},
        "is_inside_eez": is_inside_eez,
        "eez_name": eez_name if is_inside_eez else None,
        "distance_to_eez_border_km": dist_eez_km,
        "distance_to_eez_border_nm": dist_eez_nm,
        "is_inside_mpa": is_inside_mpa,
        "mpa_details": mpa_details,
        "nearest_mpa": nearest_mpa,
        "coastal_sector": coastal_sector,
        "geofence_status": geofence_status,
        "advisory_message": advisory,
        "engine": "GeoPandas Spatial Engine"
    }

def check_point_boundaries(engine: Optional[Engine], lat: float, lon: float) -> Dict[str, Any]:
    """
    Performs spatial containment and distance queries.
    Uses PostGIS if connected, with automatic fallback to GeoPandas in-memory engine.
    """
    if engine:
        pg_res = _check_boundaries_postgis(engine, lat, lon)
        if pg_res:
            return pg_res
    return _check_boundaries_geopandas(lat, lon)

def get_geofence_status(engine: Optional[Engine], lat: float, lon: float) -> Dict[str, Any]:
    """
    Streamlined geofence safety evaluation for vessel monitoring and HUD display.
    """
    boundary_info = check_point_boundaries(engine, lat, lon)
    return {
        "lat": lat,
        "lon": lon,
        "status": boundary_info["geofence_status"],
        "advisory": boundary_info["advisory_message"],
        "is_inside_eez": boundary_info["is_inside_eez"],
        "is_inside_mpa": boundary_info["is_inside_mpa"],
        "nearest_mpa": boundary_info["nearest_mpa"],
        "coastal_sector": boundary_info["coastal_sector"]
    }

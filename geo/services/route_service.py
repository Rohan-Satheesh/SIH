"""
NeerMitra Geospatial Intelligence Engine - Route Risk Service
Implements Task 5 of the Geospatial & Map Services Roadmap.
"""

from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy import text
from sqlalchemy.engine import Engine
from shapely.geometry import Point, LineString
import math

from geo.services.boundary_service import check_point_boundaries, haversine_distance

def interpolate_segment_points(p1: Tuple[float, float], p2: Tuple[float, float], interval_km: float = 15.0) -> List[Tuple[float, float]]:
    """
    Interpolates intermediate lat/lon points along a geodesic route line.
    """
    lat1, lon1 = p1
    lat2, lon2 = p2
    
    total_dist = haversine_distance(lat1, lon1, lat2, lon2)
    steps = max(1, int(total_dist / interval_km))
    points = []
    
    for i in range(steps + 1):
        fraction = i / float(steps)
        ilat = lat1 + (lat2 - lat1) * fraction
        ilon = lon1 + (lon2 - lon1) * fraction
        points.append((round(ilat, 4), round(ilon, 4)))
        
    return points

def analyze_route_risk(engine: Optional[Engine], waypoints: List[Tuple[float, float]]) -> Dict[str, Any]:
    """
    Samples coordinates along a vessel polyline and checks for:
    1. Intersections with Marine Protected Areas (MPAs)
    2. International EEZ Boundary breaches
    3. Weather / wave risk thresholds
    4. Generates GeoJSON colored route segments for frontend map rendering.
    """
    if len(waypoints) < 2:
        return {"error": "At least 2 waypoints are required to form a navigational route."}

    interpolated_track: List[Tuple[float, float]] = []
    for i in range(len(waypoints) - 1):
        segment_points = interpolate_segment_points(waypoints[i], waypoints[i+1], interval_km=15.0)
        interpolated_track.extend(segment_points[:-1])
    interpolated_track.append(waypoints[-1])

    waypoint_evaluations: List[Dict[str, Any]] = []
    has_mpa_violation = False
    has_eez_exit = False
    max_risk_score = 0
    total_distance_km = 0.0

    for idx, (lat, lon) in enumerate(interpolated_track):
        # Perform boundary & geofence evaluation for this point
        b_res = check_point_boundaries(engine, lat, lon)
        
        point_risk = 12 # Base nominal voyage risk
        flags = []

        if not b_res["is_inside_eez"]:
            has_eez_exit = True
            point_risk += 35
            flags.append(f"INTERNATIONAL_WATERS (Exited EEZ by {b_res['distance_to_eez_border_nm']} NM)")

        if b_res["is_inside_mpa"]:
            has_mpa_violation = True
            point_risk += 55
            flags.append(f"CRITICAL_MPA_BREACH: {b_res['nearest_mpa']['name']}")
        elif b_res["nearest_mpa"] and b_res["nearest_mpa"]["distance_km"] < 10.0:
            point_risk += 20
            flags.append(f"MPA_PROXIMITY: {b_res['nearest_mpa']['name']} ({b_res['nearest_mpa']['distance_km']} km)")

        # Calculate cumulative distance
        if idx > 0:
            prev_lat, prev_lon = interpolated_track[idx - 1]
            seg_dist = haversine_distance(prev_lat, prev_lon, lat, lon)
            total_distance_km += seg_dist

        final_score = min(100, point_risk)
        max_risk_score = max(max_risk_score, final_score)

        waypoint_evaluations.append({
            "waypoint_index": idx,
            "lat": lat,
            "lon": lon,
            "is_inside_eez": b_res["is_inside_eez"],
            "is_inside_mpa": b_res["is_inside_mpa"],
            "risk_score": final_score,
            "risk_level": "LOW" if final_score < 30 else "MEDIUM" if final_score < 60 else "HIGH",
            "flags": flags
        })

    overall_safety_rating = "SAFE" if max_risk_score < 30 else "CAUTION" if max_risk_score < 60 else "CRITICAL_HAZARD"

    # Build GeoJSON Segment Features for map visualization
    route_features = []
    for i in range(len(waypoint_evaluations) - 1):
        pt1 = waypoint_evaluations[i]
        pt2 = waypoint_evaluations[i+1]
        seg_risk = max(pt1["risk_score"], pt2["risk_score"])
        seg_color = "#10b981" if seg_risk < 30 else "#f59e0b" if seg_risk < 60 else "#ef4444"

        route_features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [pt1["lon"], pt1["lat"]],
                    [pt2["lon"], pt2["lat"]]
                ]
            },
            "properties": {
                "segment_index": i,
                "risk_score": seg_risk,
                "color": seg_color,
                "flags": pt1["flags"] + pt2["flags"]
            }
        })

    return {
        "total_distance_km": round(total_distance_km, 1),
        "total_distance_nm": round(total_distance_km / 1.852, 1),
        "sampled_waypoints_count": len(interpolated_track),
        "max_risk_score": max_risk_score,
        "overall_safety_rating": overall_safety_rating,
        "has_mpa_violation": has_mpa_violation,
        "has_eez_exit": has_eez_exit,
        "geojson_route": {
            "type": "FeatureCollection",
            "features": route_features
        },
        "track_points": waypoint_evaluations
    }

evaluate_route_risk = analyze_route_risk

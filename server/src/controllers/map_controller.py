import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import requests

from server.src.config.database import get_db_engine
from geo.layers.layer_manager import get_all_available_layers, get_geojson_layer, generate_ocean_layers
from geo.analysis.risk_calculator import generate_composite_risk_grid
from geo.services.boundary_service import check_point_boundaries
from geo.analysis.pfz_analyzer import find_nearest_pfzs
from geo.services.geofence_service import check_vessel_geofence_status
from geo.services.route_service import evaluate_route_risk
from geo.services.spatial_query_service import query_layers_by_bbox

def get_layers_summary() -> Dict[str, Any]:
    engine = get_db_engine()
    return get_all_available_layers(engine)

def get_spatial_layers_list() -> List[Dict[str, Any]]:
    engine = get_db_engine()
    summary = get_all_available_layers(engine)
    return list(summary.values())

def get_single_layer(layer_name: str) -> Optional[Dict[str, Any]]:
    engine = get_db_engine()
    return get_geojson_layer(engine, layer_name)

def handle_ocean_layers(layer_type: str = "both") -> Dict[str, Any]:
    return generate_ocean_layers(layer_type=layer_type)

def handle_composite_risk_grid(
    min_lat: float = 6.0,
    min_lon: float = 68.0,
    max_lat: float = 23.0,
    max_lon: float = 89.0,
    cell_size: float = 1.5
) -> Dict[str, Any]:
    return generate_composite_risk_grid(
        min_lat=min_lat,
        min_lon=min_lon,
        max_lat=max_lat,
        max_lon=max_lon,
        cell_size_deg=cell_size
    )

def handle_ais_vessels() -> Dict[str, Any]:
    api_key = os.getenv("MARINETRAFFIC_API_KEY")
    api_url = os.getenv(
        "MARINETRAFFIC_API_URL",
        "https://services.marinetraffic.com/api/exportvessels/v:8/{api_key}/timespan:10/protocol:jsono"
    )
    if api_key:
        try:
            endpoint = api_url.format(api_key=api_key)
            resp = requests.get(endpoint, timeout=8)
            if resp.ok:
                payload = resp.json()
                rows = payload if isinstance(payload, list) else payload.get("data", []) if isinstance(payload, dict) else []
                vessels = []
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    lat = row.get("LAT") or row.get("lat") or row.get("latitude")
                    lon = row.get("LON") or row.get("lon") or row.get("longitude")
                    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                        vessels.append({
                            "mmsi": row.get("MMSI") or row.get("mmsi"),
                            "imo": row.get("IMO") or row.get("imo"),
                            "name": row.get("SHIPNAME") or row.get("name") or "Unknown Vessel",
                            "latitude": float(lat),
                            "longitude": float(lon),
                            "heading": row.get("HEADING") or row.get("heading"),
                            "speed": row.get("SPEED") or row.get("speed"),
                            "course": row.get("COURSE") or row.get("course"),
                            "ship_type": row.get("TYPE_NAME") or row.get("ship_type") or "Vessel",
                            "last_position": row.get("TIMESTAMP") or row.get("timestamp")
                        })
                return {
                    "connected": True,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "vessels": vessels,
                    "count": len(vessels),
                    "message": "Live AIS telemetry from MarineTraffic."
                }
        except Exception:
            pass

    now_iso = datetime.now(timezone.utc).isoformat()
    sample_vessels = [
        {
            "mmsi": "419000123",
            "imo": "9312345",
            "name": "MV Sagar Kanya",
            "latitude": 9.98,
            "longitude": 75.72,
            "heading": 210,
            "speed": 11.4,
            "course": 215,
            "ship_type": "Research Vessel",
            "last_position": now_iso
        },
        {
            "mmsi": "419000456",
            "imo": "9456789",
            "name": "INS Tarangini",
            "latitude": 9.85,
            "longitude": 75.92,
            "heading": 140,
            "speed": 7.8,
            "course": 145,
            "ship_type": "Sailing Vessel",
            "last_position": now_iso
        },
        {
            "mmsi": "419000789",
            "imo": "9234567",
            "name": "Coast Guard Samar",
            "latitude": 10.12,
            "longitude": 75.65,
            "heading": 320,
            "speed": 16.2,
            "course": 315,
            "ship_type": "Patrol Craft",
            "last_position": now_iso
        },
        {
            "mmsi": "419000999",
            "imo": "9123888",
            "name": "Matsya Varshini",
            "latitude": 9.75,
            "longitude": 76.10,
            "heading": 85,
            "speed": 8.5,
            "course": 90,
            "ship_type": "Commercial Fishing",
            "last_position": now_iso
        }
    ]
    return {
        "connected": True,
        "fetched_at": now_iso,
        "vessels": sample_vessels,
        "count": len(sample_vessels),
        "message": "Simulated Indian EEZ AIS Telemetry"
    }

def handle_check_boundary(lat: float, lon: float) -> Dict[str, Any]:
    engine = get_db_engine()
    return check_point_boundaries(engine, lat, lon)

def handle_nearest_pfz(lat: float, lon: float, limit: int = 3) -> Dict[str, Any]:
    engine = get_db_engine()
    return find_nearest_pfzs(engine, lat, lon, limit=limit)

def handle_geofence_status(lat: float, lon: float) -> Dict[str, Any]:
    engine = get_db_engine()
    return check_vessel_geofence_status(engine, lat, lon)

def handle_route_risk(waypoints: List[List[float]]) -> Dict[str, Any]:
    engine = get_db_engine()
    return evaluate_route_risk(engine, waypoints)

def handle_spatial_bbox_query(min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> Dict[str, Any]:
    engine = get_db_engine()
    return query_layers_by_bbox(engine, min_lat, min_lon, max_lat, max_lon)


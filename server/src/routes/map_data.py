from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from shared.schemas.geo_schema import RouteRiskRequest, SpatialQueryRequest
import server.src.controllers.map_controller as controller

router = APIRouter(prefix="/api/geo", tags=["Geospatial & Marine Maps"])

@router.get("/layers")
def get_layers():
    return controller.get_layers_summary()

@router.get("/layer/{layer_name}")
def get_layer(layer_name: str):
    res = controller.get_single_layer(layer_name)
    if not res:
        raise HTTPException(status_code=404, detail=f"Layer '{layer_name}' not found")
    return res

@router.get("/ocean-layers")
def get_ocean_layers(layer_type: str = Query("both", description="'sst', 'chlorophyll', or 'both'")):
    return controller.handle_ocean_layers(layer_type)

@router.get("/composite-risk-grid")
def get_composite_risk_grid(
    min_lat: float = Query(6.0),
    min_lon: float = Query(68.0),
    max_lat: float = Query(23.0),
    max_lon: float = Query(89.0),
    cell_size: float = Query(1.5)
):
    return controller.handle_composite_risk_grid(min_lat, min_lon, max_lat, max_lon, cell_size)

@router.get("/check-boundary")
def check_boundary(lat: float = Query(...), lon: float = Query(...)):
    return controller.handle_check_boundary(lat, lon)

@router.get("/nearest-pfz")
@router.get("/pfz")
def nearest_pfz(lat: float = Query(9.93), lon: float = Query(75.82), limit: int = Query(3, ge=1, le=10)):
    return controller.handle_nearest_pfz(lat, lon, limit)

@router.get("/geofence-alert")
def geofence_alert(lat: float = Query(...), lon: float = Query(...)):
    return controller.handle_geofence_status(lat, lon)

@router.post("/route-risk")
def route_risk(req: RouteRiskRequest):
    return controller.handle_route_risk(req.waypoints)

@router.post("/spatial-query")
def spatial_query(req: SpatialQueryRequest):
    return controller.handle_spatial_bbox_query(req.min_lat, req.min_lon, req.max_lat, req.max_lon)

# Dedicated Spatial Layer Router matching frontend endpoints
spatial_router = APIRouter(prefix="/api/spatial", tags=["Spatial Layers"])

@spatial_router.get("/layers")
def list_spatial_layers():
    return {"layers": controller.get_spatial_layers_list()}

@spatial_router.get("/layers/{layer_name}")
def get_spatial_layer(layer_name: str):
    res = controller.get_single_layer(layer_name)
    if not res:
        raise HTTPException(status_code=404, detail=f"Layer '{layer_name}' not found")
    return res

# Dedicated AIS Telemetry Router
ais_router = APIRouter(prefix="/api/ais", tags=["AIS Telemetry"])

@ais_router.get("/vessels")
def get_ais_vessels():
    return controller.handle_ais_vessels()

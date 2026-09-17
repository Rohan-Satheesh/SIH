from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point


EEZ_FILE = Path(
    "geo/data/boundaries/world_eez/"
    "World_EEZ_v12_20231025/eez_v12.shp"
)


def check_india_eez(latitude: float, longitude: float) -> dict:
    """Check whether a coordinate is inside India's EEZ."""

    if not (-90 <= latitude <= 90):
        return {"status": "error", "message": "Invalid latitude"}

    if not (-180 <= longitude <= 180):
        return {"status": "error", "message": "Invalid longitude"}

    if not EEZ_FILE.exists():
        return {"status": "error", "message": "EEZ shapefile not found"}

    india_eez = gpd.read_file(EEZ_FILE)
    india_eez = india_eez[
        india_eez["SOVEREIGN1"].astype(str).str.lower() == "india"
    ]

    point = Point(longitude, latitude)

    inside = india_eez.contains(point).any()

    return {
        "status": "success",
        "latitude": latitude,
        "longitude": longitude,
        "is_inside_eez": bool(inside),
        "source": "Marine Regions World EEZ v12",
    }


def distance_to_india_sri_lanka_boundary(
    latitude: float,
    longitude: float,
) -> dict:
    """Calculate approximate distance to the India-Sri Lanka boundary."""

    boundary_file = Path(
        "geo/data/boundaries/world_eez/"
        "World_EEZ_v12_20231025/eez_boundaries_v12.shp"
    )

    boundaries = gpd.read_file(boundary_file)

    sri_lanka_india = boundaries[
        boundaries["LINE_NAME"].astype(str).str.contains(
            "Sri Lanka - India",
            case=False,
            na=False,
        )
    ]

    point = gpd.GeoSeries(
        [Point(longitude, latitude)],
        crs="EPSG:4326",
    ).to_crs("EPSG:3857")

    boundary_projected = sri_lanka_india.to_crs("EPSG:3857")

    distance_m = boundary_projected.geometry.distance(point.iloc[0]).min()

    return {
        "status": "success",
        "latitude": latitude,
        "longitude": longitude,
        "distance_to_boundary_km": float(round(distance_m / 1000, 2)),
        "nearest_boundary": "India-Sri Lanka",
    }

GEOSPATIAL_TOOLS = [
    check_india_eez,
    distance_to_india_sri_lanka_boundary,
]
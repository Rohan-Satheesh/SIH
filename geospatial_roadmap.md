# Geospatial & Map Services Engineer Roadmap

Welcome to the team! Your role is critical because you are building the "spatial brain" of the NeerMitra platform. Every vessel route, marine warning, and fishing zone query relies on the geospatial foundation you are about to lay down.

Currently, the `backend/main.py` is returning mock data for vessels and PFZ (Potential Fishing Zones). Your job is to replace those mocks with real, spatially-aware logic using PostGIS and Python.

Here is a structured, step-by-step walkthrough of how you should approach your 10 tasks, grouped logically into four phases.

---

## Phase 1: The Foundation (Data & Infrastructure)
*Before you can build services, you need a place to put the data.*

### 1. Boundary Data Setup (Task 1)
- **What to do:** Download EEZ (Exclusive Economic Zones), MPA (Marine Protected Areas), and territorial water data.
- **Tools:** Natural Earth, MarineRegions.org, or Indian government sources.
- **Tech Setup:** You will need a PostgreSQL database with the **PostGIS** extension installed.
- **Action:** Write a Python script using `geopandas` and `sqlalchemy` (with `geoalchemy2`) to read these GeoJSON/Shapefiles and load them into your PostGIS database as `Geometry` or `Geography` columns.

---

## Phase 2: Core Spatial APIs
*Now that data is in the database, let's expose it via FastAPI.*

### 2. Boundary Check Service (Task 2)
- **What to do:** Create `backend/boundary_service.py`.
- **Logic:** Write a function that takes a `(lat, lon)`, converts it to a PostGIS point (`ST_SetSRID(ST_MakePoint(lon, lat), 4326)`), and runs an `ST_Contains` query against your boundary tables.
- **Endpoint:** Connect this to a FastAPI route (e.g., `GET /api/geo/check-boundary?lat=X&lon=Y`).

### 3. Nearest PFZ Calculator (Task 4)
- **What to do:** Currently, `/api/pfz` returns mock data. You need to calculate the *real* nearest zone.
- **Logic:** Fetch today's PFZ data (from B2 or Postgres). Given a user's location, use PostGIS `<->` (nearest neighbor operator) or Python's `shapely`/`scipy.spatial.KDTree` to find the closest points, and calculate bearing (angle) and distance.

---

## Phase 3: Advanced Spatial Monitoring
*Moving from static lookups to dynamic, route-based analysis.*

### 4. Geofence Monitoring (Task 3)
- **What to do:** Create `backend/geofence_service.py`.
- **Logic:** This is an extension of Task 2. Instead of just checking if a point is *inside*, use `ST_Distance` to check if a user is approaching an MPA or restricted zone. If distance < threshold, trigger an alert.

### 5. Route Risk Analysis (Task 5)
- **What to do:** Create `backend/route_service.py`.
- **Logic:** The frontend will send a polyline (an array of lat/lon points). You need to use `shapely` to interpolate points along this line (e.g., every 10km). For each point, query your weather/wave/current data, and return a GeoJSON `FeatureCollection` coloring the route segments by risk.

### 6. Spatial Query Service (Task 8)
- **What to do:** Create `backend/spatial_query_service.py`.
- **Logic:** When the AI agent asks "What's the weather like in the Arabian Sea?", you need an API that accepts a Bounding Box (BBOX) or Polygon, and uses `ST_Intersects` to aggregate all alerts, SST, and chlorophyll data within that polygon.

---

## Phase 4: Map Serving & Analytics (B2 & Fast Rendering)
*Optimizing the data for the frontend map (Leaflet/Mapbox/Deck.gl).*

### 7. SST / Chlorophyll Layer Service (Task 6)
- **What to do:** Marine data (SST, Chlorophyll) is heavy. You can't send megabytes of raw data to the frontend.
- **Logic:** Read the raw data from your B2 bucket. Serve it as filtered GeoJSON. If it's raster data, you might need to contour it (using `matplotlib.contour` or `gdal_contour`) into polygons before sending it.

### 8. Composite Risk Layer (Task 7)
- **What to do:** Create a heatmap.
- **Logic:** Normalize wind, wave, and alert data to a 0-100 scale. Create a regular grid (Hexagons or squares using `h3-py` or PostGIS `ST_HexagonGrid`), assign scores to each grid cell, and serve this as a GeoJSON layer.

### 9. Trend Analysis (Task 9)
- **What to do:** Create `backend/trend_analyzer.py`.
- **Logic:** Query 7-day/30-day historical data from B2. Calculate averages and standard deviations. If today's SST is 2 standard deviations above the 30-day average, flag it as a "Marine Heatwave".

### 10. GeoJSON Optimization (Task 10)
- **What to do:** Fast frontend rendering.
- **Logic:** Before returning huge GeoJSON polygons (like the complex Indian coastline), use Shapely's `simplify(tolerance=0.01)` or PostGIS `ST_SimplifyPreserveTopology`. Cache the simplified results using Redis or in-memory Python LRU cache.

---

## How to begin today:

I recommend starting with **Phase 1**.
Do you have a local PostgreSQL instance running with PostGIS installed?
If yes, I can write the Python data ingestion script (Task 1) for you right now using `geopandas` and `sqlalchemy`. We can create a new `backend/geo/` directory to house your specific services cleanly alongside the main API.

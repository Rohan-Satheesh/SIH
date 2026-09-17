# Dead Code Audit Report

## Summary

A comprehensive multi-angle audit was conducted across the active React 19/Vite frontend, the modular 6-role FastAPI backend, geospatial engines, NLP engines, data pipelines, shared contracts, configuration files, build scripts, and legacy directories.

Total identified dead code elements:
- **Legacy / Duplicate Directories for Deletion**:
  - `backend/` (Legacy monolithic backend directory containing 14+ files including `main.py`, `agent_engine.py`, `test_geo_suite.py`, duplicate `geo/` services, duplicate `data/` geojson files, and scripts).
  - `client/` (Redundant duplicate mirror of the root frontend directory containing 10+ duplicate files).
- **Unused Frontend Components**:
  - `src/components/hud/StatusIndicator.tsx` (Completely unreferenced and not imported by any active page or component).
- **Empty / Stub Module Directories**:
  - `server/src/models/` (Empty placeholder directory; all schemas reside in `shared/schemas/`).
  - `server/src/services/` (Empty placeholder directory; services reside in `geo/services/`).
  - `server/src/websocket/` (Empty placeholder directory; no active websocket channels).
  - `agents/agents/` (Empty placeholder directory; agent logic resides in `agents/orchestrator/` and `agents/tools/`).
  - `agents/planner/` (Empty placeholder directory).
  - `pipeline/storage/` (Empty placeholder directory).
- **Legacy Compatibility Stub Files**:
  - `geo/services/ocean_layers_service.py` (One-line wildcard import alias superseded by `geo.layers.layer_manager`).
  - `geo/services/pfz_service.py` (One-line wildcard import alias superseded by `geo.analysis.pfz_analyzer`).
  - `geo/services/risk_grid_service.py` (One-line wildcard import alias superseded by `geo.layers.layer_manager`).
- **Unused Utility Functions & Helper Methods**:
  - `shared/utils/date_utils.py`: `get_utc_timestamp_iso()`, `format_marine_datetime()`
  - `shared/utils/format_utils.py`: `format_nautical_miles()`, `format_knots()`
  - `backend/main.py`: `autonomous_marine_spatial_reasoning()`
- **Unused Variables & Constants**:
  - `backend/main.py`: `PORTS_AND_SECTORS`, unused `INDIAN_PFZ_HOTSPOTS`, `json`, `Tuple` imports.
  - `backend/agent_engine.py`: unused `json`, `get_geofence_status`, `INDIAN_PFZ_HOTSPOTS`, `analyze_route_risk` imports.

---

## Files to Delete

### 1. Legacy Monolith Backend (`backend/`)
The entire `backend/` directory is obsolete legacy code superseded by the 6-role modular monorepo architecture (`server/`, `geo/`, `agents/`, `nlp/`, `pipeline/`, and `shared/`). `run_model.js` launches `server.src.app:app`, and no active services import from `backend/`.

* `backend/main.py` — Monolithic FastAPI app (680 lines) containing obsolete endpoints and uncalled reasoning functions.
* `backend/agent_engine.py` — Old monolithic agent implementation (750 lines) superseded by `agents/orchestrator/graph.py`.
* `backend/test_geo_suite.py` — Legacy standalone smoke-test script targeting the old monolith.
* `backend/requirements.txt` — Duplicate requirements file superseded by `server/requirements.txt`.
* `backend/.env` & `backend/.env.example` — Redundant environment files superseded by root `.env`.
* `backend/scripts/load_boundaries.py` — Legacy boundary loader superseded by `geo/services/boundary_service.py`.
* `backend/geo/boundary_service.py` — Duplicate of `geo/services/boundary_service.py`.
* `backend/geo/pfz_service.py` — Duplicate of `geo/analysis/pfz_analyzer.py`.
* `backend/geo/route_service.py` — Duplicate of `geo/services/route_service.py`.
* `backend/geo/spatial_cache.py` — Duplicate of `geo/services/spatial_cache.py`.
* `backend/geo/spatial_query_service.py` — Duplicate of `geo/services/spatial_query_service.py`.
* `backend/geo/trend_analyzer.py` — Duplicate of `geo/analysis/trend_analyzer.py`.
* `backend/geo/risk_grid_service.py` — Duplicate of `geo/layers/risk_layer.py`.
* `backend/geo/ocean_layers_service.py` — Duplicate of `geo/layers/layer_manager.py`.
* `backend/data/india_eez_boundaries.geojson` — Duplicate of `geo/boundaries/india_eez_boundaries.geojson` (2.38 MB).
* `backend/data/india_marine_protected_areas.geojson` — Duplicate of `geo/boundaries/india_marine_protected_areas.geojson`.
* `backend/data/india_coastal_fishing_sectors.geojson` — Duplicate of `geo/boundaries/india_coastal_fishing_sectors.geojson`.

### 2. Redundant Client Directory (`client/`)
The active web application is served from the root workspace (`src/`, `index.html`, `vite.config.ts`, and root `package.json`). `client/` is a redundant mirror directory containing duplicate source files and node configurations.

* `client/src/` (All mirrored components, pages, and assets)
* `client/package.json`
* `client/vite.config.ts`
* `client/tsconfig.json`, `client/tsconfig.app.json`, `client/tsconfig.node.json`
* `client/index.html`
* `client/dist/`
* `client/node_modules/`

### 3. Unused Frontend Component
* `src/components/hud/StatusIndicator.tsx` — 70 lines. A standalone HUD connectivity indicator that is neither imported nor rendered by any active page (`App.tsx`, `HomeDashboard.tsx`, `FishermanMode.tsx`, etc.).

### 4. Legacy Compatibility Alias Stubs
* `geo/services/ocean_layers_service.py` — 3 lines. Stub containing wildcard import `from geo.layers.layer_manager import *`.
* `geo/services/pfz_service.py` — 3 lines. Stub containing wildcard import `from geo.analysis.pfz_analyzer import *`.
* `geo/services/risk_grid_service.py` — 3 lines. Stub containing wildcard import `from geo.layers.layer_manager import *`.

### 5. Empty Placeholder Directories
* `server/src/models/__init__.py`
* `server/src/services/__init__.py`
* `server/src/websocket/__init__.py`
* `agents/agents/__init__.py`
* `agents/planner/__init__.py`
* `pipeline/storage/__init__.py`

---

## Functions/Methods to Delete

### `backend/main.py`
* `autonomous_marine_spatial_reasoning()` — Legacy 150-line heuristic reasoning function. Has no callers or endpoint bindings in the active system.

### `shared/utils/date_utils.py`
* `get_utc_timestamp_iso()` — Helper generating UTC ISO timestamp string; unreferenced across all modules.
* `format_marine_datetime(dt)` — Formatting helper for marine datetime stamps; unreferenced across all modules.

### `shared/utils/format_utils.py`
* `format_nautical_miles(nm, decimals)` — Helper for NM string formatting; all active modules format inline or via TypeScript utilities.
* `format_knots(speed_kts)` — Helper for knots formatting; unreferenced across all modules.

---

## Classes to Delete

No active classes are marked for deletion. All classes in active modules (`Pydantic` models in `shared/schemas/`, layer managers in `geo/layers/`, and memory stores in `agents/memory/`) are actively referenced. Legacy classes within `backend/main.py` and `backend/agent_engine.py` will be removed upon deletion of the `backend/` directory.

---

## Variables/Constants to Delete

### `backend/main.py`
* `PORTS_AND_SECTORS` — Private dictionary constant iterated exclusively within `autonomous_marine_spatial_reasoning()`.
* Unused imports: `json`, `Tuple` from `typing`, `INDIAN_PFZ_HOTSPOTS` from `geo.pfz_service`.

### `backend/agent_engine.py`
* Unused imports: `json`, `get_geofence_status`, `INDIAN_PFZ_HOTSPOTS`, `analyze_route_risk`.

---

## Verification Notes

1. **Static Analysis**: Traced all import statements, module exports, and symbol usages across TypeScript (`src/`) and Python (`server/`, `geo/`, `agents/`, `nlp/`, `pipeline/`, `shared/`).
2. **Entry Point Analysis**:
   - Frontend bootstrap: `index.html` ➔ `src/main.tsx` ➔ `src/App.tsx`. All active routes (`/`, `/dashboard`, `/weather`, `/sea`, `/zones`, `/fisherman`, `/assistant`, `/safety`, `/fleet`, `/data-sources`, `/command-center`, `/landing`) map to verified files in `src/pages/`.
   - Backend gateway: `run_model.js` executes `python -m uvicorn server.src.app:app --reload --port 8000`. `server/src/app.py` mounts `chat_router`, `geo_router`, `health_router`, and `spatial_router`.
   - The legacy `backend/main.py` is not launched by any script or Docker service.
3. **Dynamic / Reflection Check**: Checked for dynamic imports or reflection-based invocation (`getattr`, `importlib`, `React.lazy`). None are used for the identified dead files.
4. **Data Verification**: Verified that deleting `backend/data/` does not impact geospatial boundary services, as `geo/services/boundary_service.py` and `geo/layers/layer_manager.py` load directly from `geo/boundaries/`.

---

## Estimated Impact

* **Files to Delete**: 30+ files across `backend/`, `client/`, and `src/components/hud/`
* **Lines of Code to Remove**:
  * Legacy backend (`backend/`): ~2,500 lines of Python code + 2.4 MB GeoJSON data
  * Redundant client mirror (`client/`): ~3,000 lines of duplicate TypeScript / config code
  * Dead UI components & unused utilities: ~120 lines
* **Total Impact**: **~5,600+ lines of code removed** and **~2.5 MB disk space reclaimed**, significantly streamlining build times, linting overhead, and repository maintainability.

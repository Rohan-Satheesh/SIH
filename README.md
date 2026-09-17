# NeerMitra (നീർമിത്ര) — Marine Intelligence & Coastal Safety Platform

> Real-time oceanographic telemetry, Potential Fishing Zone (PFZ) mapping, and coastal safety navigation designed for Indian fishermen and maritime fleets.

---

## 🏗️ Architecture & 6-Role Engineering Model

NeerMitra is built as a modular monorepo structured around **6 specialized engineering roles**, decoupled yet interconnected through strict shared contracts and clean API boundaries:

```mermaid
graph TD
    subgraph Role1["ROLE 1: Frontend (Client)"]
        UI["React 19 + Vite Web App"]
        MAP["Leaflet Marine Map + Spatial Layers"]
        STATE["Bilingual State (EN / ML)"]
    end

    subgraph Role2["ROLE 2: Backend (Gateway)"]
        FASTAPI["FastAPI App Gateway (:8000)"]
        ROUTERS["Routers (/api/geo, /api/spatial, /api/chat, /api/ais)"]
    end

    subgraph Role3["ROLE 3: AI Agent Swarm"]
        GRAPH["Orchestrator Graph & Router"]
        AGENTS["WeatherAgent · GeospatialAgent · SafetyAgent"]
        LLM["LLM Engine (Gemini / Grok / Local Fallback)"]
    end

    subgraph Role4["ROLE 4: Data Pipeline"]
        INGEST["INCOIS Scraper & IMD Ingestion"]
        PROCESS["Satellite SST & Chlorophyll Normalizer"]
    end

    subgraph Role5["ROLE 5: Geospatial Engine"]
        POSTGIS["PostGIS Spatial Database / Engine"]
        LAYERS["EEZ 200 NM · MPAs · SST Fronts · Fishing Sectors"]
        GEO_SRV["Haversine/Vincenty Geodesic Services"]
    end

    subgraph Role6["ROLE 6: NLP & Multilingual"]
        LANG_DET["Script Language Detector"]
        INTENT["Intent Classifier (PFZ, Weather, Geofence)"]
        RAG["Domain RAG Knowledge Retriever"]
    end

    subgraph Shared["SHARED CONTRACTS"]
        SCHEMAS["Pydantic Schemas & GeoJSON Models"]
        CONSTANTS["Coastal Sectors & EEZ Bounds"]
    end

    UI --> FASTAPI
    MAP --> ROUTERS
    ROUTERS --> GRAPH
    ROUTERS --> POSTGIS
    GRAPH --> AGENTS
    AGENTS --> GEO_SRV
    AGENTS --> LLM
    GRAPH --> INTENT
    INTENT --> LANG_DET
    INGEST --> PROCESS
    PROCESS --> POSTGIS
    FASTAPI -.-> SCHEMAS
    GRAPH -.-> SCHEMAS
    GEO_SRV -.-> CONSTANTS
```

---

## 🚀 Quick Start Guide

### ⚡ One-Command Startup (`run model`)

Launch both the **FastAPI Backend (:8000)** and **React Frontend (:5173)** concurrently in a single terminal with automated dependency resolution:

```bash
# Windows Command Prompt or PowerShell:
run model
# or
npm run run-model
# or
node run_model.js
```

> **Smart Pre-Flight Installer**: The runner inspects your Python environment and frontend `node_modules`. If any required package (`fastapi`, `uvicorn`, `pydantic`, etc.) is missing, it auto-installs them before launching.

Once started, the platform will be live at:
* **Frontend Web Application**: [http://localhost:5173](http://localhost:5173)
* **FastAPI Backend API**: [http://localhost:8000](http://localhost:8000)
* **Interactive OpenAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Alternative ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🛠️ How Every Role Works (Deep Dive)

### 🌊 ROLE 1: Frontend Engineer (`src/` & `client/src/`)
* **Core Technologies**: React 19, Vite, Tailwind CSS v4, Leaflet, React-Leaflet, Framer Motion, Lucide Icons.
* **Workspace Directory**: `src/` (mirrored in `client/src/` for standalone client builds).

#### Key Components & Responsibilities:
1. **Interactive Full-Screen Marine Map (`components/map/MarineMap.tsx`)**:
   - **CARTO Dark Matter Basemap**: Optimized for low-light night navigation at sea.
   - **Dynamic PostGIS Vector Overlays**: Real-time rendering of India EEZ boundaries, Marine Protected Areas (MPAs), SST thermal fronts, and Chlorophyll bio-plumes via `<GeoJSON>`.
   - **Interactive Pinpointing & Sector Snapping**: Clicking anywhere at sea queries the nearest Indian coastal sector with geodesic distance (`km off [Sector]`).
   - **Spatial Feature Inspector**: Floating drawer inspecting properties of clicked maritime entities with lineage explanation modals.
2. **Fisherman Mode (`pages/FishermanMode.tsx`)**:
   - Streamlined, high-contrast interface designed specifically for small craft skippers and coastal fishermen.
   - Focuses strictly on full-screen map navigation, live satellite sync, and spatial layer inspection without clutter.
3. **Command Center & Tactical HUD (`pages/CommandCenter.tsx`)**:
   - Maritime operations hub with live AIS transponder feeds, ship position tracking, and embedded AI Copilot drawer.
4. **Safety & Emergency Geofencing (`pages/SafetyView.tsx`)**:
   - Proximity radar monitoring distance to international maritime boundaries (IMBL) with one-tap emergency Coast Guard dialing (`1554`).
5. **Fleet Route Optimizer (`pages/FleetOptimizer.tsx`)**:
   - Compares transit speed vs. fuel economy strategies, predicting diesel savings and CO₂ reductions across coastal corridors.
6. **Bilingual Context Provider (`contexts/LanguageContext.tsx`)**:
   - Seamless live switching between **Malayalam (`മലയാളം`)** and **English**, updating all telemetries, advisories, and map tooltips.

---

### ⚙️ ROLE 2: Backend Engineer (`server/src/` & `backend/`)
* **Core Technologies**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy, GeoAlchemy2.
* **Workspace Directory**: `server/src/` (application gateway) and `backend/`.

#### Key Modules & Responsibilities:
1. **Application Gateway (`server/src/app.py`)**:
   - Configures CORS middleware for local and production web clients.
   - Mounts decoupled modular routers:
     - `spatial_router` (`/api/spatial`): Spatial layer catalogs and GeoJSON delivery.
     - `geo_router` (`/api/geo`): Nearest PFZ calculations, EEZ boundary checks, geofence alerts.
     - `ais_router` (`/api/ais`): Real-time vessel transponder positions.
     - `chat_router` (`/api/chat`): Marine intelligence conversational agent.
     - `health_router` (`/api/health` & `/api/status`): Service diagnostics.
2. **Controllers (`server/src/controllers/`)**:
   - `map_controller.py`: Formats GeoJSON responses, handles spatial bounding box queries, and fetches live MarineTraffic AIS transponder data.
   - `chat_controller.py`: Intercepts casual conversational greetings (`is_casual_message`) for zero-latency responses, routes maritime queries to the agent orchestrator, and enforces language detection.
3. **Resilient Offline Architecture**:
   - Operates with PostGIS/PostgreSQL when configured, but automatically falls back to in-memory GeoJSON spatial data and geodesic math if the database is offline.

---

### 🧠 ROLE 3: AI Agent Engineer (`agents/`)
* **Core Technologies**: LangGraph / Multi-Agent Swarm pattern, Python, Tool Calling, Conversation Memory.
* **Workspace Directory**: `agents/`.

#### Key Modules & Responsibilities:
1. **Orchestrator Graph (`agents/orchestrator/graph.py`)**:
   - Serves as the brain of NeerMitra's conversational copilot.
   - Extracts coordinates and entities from user context or conversation history (`extract_target_location`).
   - Dispatches user intent to specialized sub-agents.
2. **Sub-Agent Swarm & Tools (`agents/tools/`)**:
   - **`WeatherAgent` (`weather_tools.py`)**: Fetches real-time marine meteorology (wave heights, swells, wind speed, wind gusts) via Open-Meteo API; computes safety risk index (`LOW`, `MEDIUM`, `HIGH`).
   - **`GeospatialAgent` (`geofence_tools.py`)**: Queries spatial indices to locate top high-yield PFZ zones with bearing and distance.
   - **`SafetyGeofenceAgent` (`geofence_tools.py`)**: Determines proximity to Indian EEZ borders and restricted Marine Protected Areas.
   - **`OceanTrendExplainerAgent` (`ocean_tools.py`)**: Provides scientific oceanographic explanations for sea surface temperature anomalies.
3. **Session & Conversation Memory (`agents/memory/`)**:
   - `conversation_memory.py`: Tracks multi-turn conversational context keyed by `session_id`.
   - `context_store.py`: Remembers the user's active fishing vessel, port of departure, and language preferences across turns.
4. **LLM Provider Flexibility (`backend/agent_engine.py`)**:
   - **Google Gemini 2.5 Flash**: Native function calling with structured schema outputs.
   - **OpenAI-Compatible APIs (Grok / Groq)**: Easily integrated via standard REST completions endpoints (`api.x.ai/v1` or `api.groq.com/openai/v1`).
   - **Deterministic Fallback**: Generates structured, verified marine recommendations even without external LLM API keys.

---

### 🛰️ ROLE 4: Data Pipeline Engineer (`pipeline/`)
* **Core Technologies**: Python, Requests, BeautifulSoup, Pandas, GeoPandas, Cron/Task Schedulers.
* **Workspace Directory**: `pipeline/`.

#### Key Modules & Responsibilities:
1. **Automated Ingestion (`pipeline/ingestion/`)**:
   - `incois_scraper.py`: Periodically harvests advisories from INCOIS (Indian National Centre for Ocean Information Services), extracting SST frontal zones, Chlorophyll-a bio-plumes, and PFZ coordinates.
   - `imd_scraper.py`: Ingests Indian Meteorological Department (IMD) marine weather warnings, cyclone alerts, and rough sea bulletins.
2. **Data Processors & Normalizers (`pipeline/processors/`)**:
   - Cleans coordinate anomalies and projects raw coordinates into standardized EPSG:4326 GeoJSON polygons.
   - Computes thermal-chlorophyll overlap indices to calculate pelagic fish species yield confidence (`HIGH`, `MEDIUM`, `MODERATE`).
3. **Schedulers (`pipeline/schedulers/`)**:
   - Triggers ingestion runs aligned with daily satellite passes (06:00 UTC and 18:00 UTC) to keep ocean telemetry current.

---

### 🗺️ ROLE 5: Geospatial Engineer (`geo/`)
* **Core Technologies**: PostGIS, GeoPandas, Shapely, GeoJSON, Geodesic Algorithms (Haversine & Vincenty), EPSG:4326.
* **Workspace Directory**: `geo/`.

#### Key Modules & Responsibilities:
1. **Spatial Layer Management (`geo/layers/layer_manager.py`)**:
   - Manages official maritime shapefiles and vector features:
     - `india_eez_boundaries`: Complete 200 Nautical Mile Indian Exclusive Economic Zone perimeter.
     - `india_marine_protected_areas`: Wildlife sanctuaries, coral reserves, and no-fishing zones.
     - `india_coastal_fishing_sectors`: Designated state maritime sectors (Kochi, Munambam, Alappuzha, Goa, Mumbai, Mangalore, Kutch, Chennai, Vizag, Paradip, Sundarbans).
     - `sst_thermal_fronts`: Sea Surface Temperature gradient polygons indicating nutrient upwelling.
     - `chlorophyll_blooms`: Satellite bio-plumes identifying plankton-rich aggregation spots.
     - `composite_risk_grid`: Hexagonal grid scoring composite ocean risk (depth + wave height + vessel traffic).
2. **Spatial Services (`geo/services/`)**:
   - `boundary_service.py`: Computes point-in-polygon containment and exact distance-to-boundary in Nautical Miles (NM).
   - `geofence_service.py`: High-speed proximity alerts alerting vessels before crossing into international or protected waters.
   - `spatial_cache.py`: High-performance in-memory cache delivering GeoJSON layers to the frontend with sub-10ms latency.

---

### 🗣️ ROLE 6: NLP & Multilingual Engineer (`nlp/`)
* **Core Technologies**: Python, Regex, Sentence Embeddings, Malayalam Unicode Tokenizers, RAG (Retrieval-Augmented Generation).
* **Workspace Directory**: `nlp/`.

#### Key Modules & Responsibilities:
1. **Language Detection (`nlp/detection/language_detector.py`)**:
   - Inspects Malayalam Unicode codepoints (`\u0D00-\u0D7F`) and token patterns to instantly detect whether a query is in Malayalam or English.
2. **Intent Classification (`nlp/detection/intent_classifier.py`)**:
   - Uses domain-specific keyword and regex heuristics to map queries into structured intent classes:
     - `pfz`: Queries about fish availability, fishing spots, or species.
     - `weather`: Questions about waves, wind, swells, or navigation safety.
     - `boundary`: Questions about EEZ limits, border security, or restricted waters.
     - `sos`: Distress calls and Coast Guard hotline queries.
     - `trend`: Long-term oceanographic patterns or temperature anomalies.
3. **Domain RAG Retriever (`nlp/rag/`)**:
   - `document_loader.py` & `retriever.py`: Indexes marine safety handbooks, seasonal fishing ban schedules, and fish species behaviors to ground AI responses in factual oceanographic documentation.

---

### 📦 Shared Contracts & Schemas (`shared/`)
* **Workspace Directory**: `shared/`.
* **`schemas/chat_schema.py`**: Defines `ChatRequest` and `CopilotResponse` Pydantic models ensuring backend and frontend adhere to identical request/response contracts.
* **`schemas/geo_schema.py`**: Standardizes GeoJSON geometries, coordinate pairs, and spatial feature properties.
* **`constants/`**: Holds canonical coordinates for major Indian fishing ports, coastal sectors, and nautical conversion formulas (`1 NM = 1.852 km`).

---

## 🔄 End-to-End Request Lifecycle

Here is how all 6 roles collaborate during a typical user interaction:

```
[User speaks/types in Malayalam on Web App (Role 1)]
                         │
                         ▼
[POST /api/chat received by FastAPI Gateway (Role 2)]
                         │
                         ▼
[Language Detector identifies Malayalam script (Role 6)]
                         │
                         ▼
[Intent Classifier categorizes query as 'pfz' (Role 6)]
                         │
                         ▼
[Agent Orchestrator extracts location & invokes GeospatialAgent (Role 3)]
                         │
                         ▼
[Geospatial Service calculates nearest PFZ via Haversine / PostGIS (Role 5)]
                         │
                         ▼
[Weather Agent pulls real-time wave/wind data from Open-Meteo (Role 3)]
                         │
                         ▼
[Pipeline verifies latest satellite chlorophyll pass is synced (Role 4)]
                         │
                         ▼
[Copilot formats structured response in Malayalam with telemetry (Role 3 / Role 2)]
                         │
                         ▼
[Interactive Leaflet Map centers pin and updates telemetry HUD (Role 1)]
```

---

## 📡 Core API Endpoints

| Method | Endpoint | Description | Responsible Role |
|---|---|---|---|
| `GET` | `/` | System status and active spatial layer catalog | Role 2 (Backend) |
| `GET` | `/api/status` | Real-time service telemetry & database health | Role 2 (Backend) |
| `GET` | `/api/geo/nearest-pfz?lat=9.93&lon=75.82&limit=3` | Returns nearest high-yield PFZs with bearing, distance & fuel | Role 5 (Geospatial) |
| `GET` | `/api/geo/check-boundary?lat=9.93&lon=75.82` | EEZ 200 NM and Marine Protected Area check | Role 5 (Geospatial) |
| `GET` | `/api/geo/geofence-alert?lat=9.93&lon=75.82` | International perimeter proximity warning | Role 5 (Geospatial) |
| `GET` | `/api/spatial/layers` | PostGIS spatial layer catalog metadata | Role 5 (Geospatial) |
| `GET` | `/api/spatial/layers/{name}` | Direct GeoJSON vector feature collection for Leaflet | Role 5 (Geospatial) |
| `GET` | `/api/ais/vessels` | Live AIS ship transponder positions | Role 2 (Backend) |
| `POST` | `/api/chat` | Multilingual agentic marine intelligence copilot | Role 3 & Role 6 |

---

## ⚙️ Environment Configuration

Create a `.env` file in the root directory:

```env
# Optional External API Keys
GEMINI_API_KEY=your_google_ai_studio_key_here
ENABLE_GEMINI_AGENT=false

# Optional xAI Grok / Groq API Keys
GROK_API_KEY=your_xai_grok_key_here
GROQ_API_KEY=your_groq_cloud_key_here

# Optional MarineTraffic AIS Key (falls back to simulated Indian coastal fleet if omitted)
MARINETRAFFIC_API_KEY=your_marinetraffic_key_here

# Optional PostgreSQL / PostGIS Database (falls back to in-memory spatial engine if omitted)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/neermitra
```

---

## 🛡️ License
Built for the Smart India Hackathon (SIH). All rights reserved.

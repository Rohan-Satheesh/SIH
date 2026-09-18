# ORCA — Marine EcOsystem Reasoning with Collaborative Agents
## Product Requirements Document (PRD) — SIH Hackathon

---

## 1. Product Overview

### 1.1 Problem Summary

Marine stakeholders (fishermen, coastal authorities, researchers, maritime operators) depend on timely oceanographic and meteorological data for safety and livelihood. Today, this data exists across **siloed, batch-driven systems** — INCOIS PFZ/OSF advisories (daily bulletins), IMD marine weather (static PDFs/web), MOSDAC satellite products (raw scientific formats) — none of which offer conversational access, multi-source reasoning, or personalized recommendations.

### 1.2 What ORCA Is

An **Agentic AI-powered conversational platform** that sits on top of existing advisory systems and global data feeds, adds multi-agent reasoning, a natural language chat interface, and geospatial context — making marine intelligence accessible to real stakeholders through simple questions like:

- *"Is it safe to go fishing tomorrow morning from Kochi?"*
- *"Where is the nearest PFZ today?"*
- *"Show me the safest route avoiding high waves and restricted zones"*

### 1.3 What ORCA Is NOT

- **Not a replacement for INCOIS/IMD** — ORCA positions official advisories (PFZ, OSF, cyclone warnings) as the authoritative layer. Global API data is a **supplementary near-real-time context layer** that fills gaps between daily advisory cycles.
- **Not claiming "live" data** — satellite EO products have inherent revisit/processing latency. We say **"near-real-time"** (refreshed every few hours) to avoid overpromising.

### 1.4 Target Users

| User | Primary Need |
|------|-------------|
| **Small-scale fishermen** | Safe trip planning, PFZ discovery, weather safety, boundary alerts |
| **Coastal authorities** | Situational awareness, disaster preparedness, enforcement |
| **Marine researchers** | Multi-parameter exploration, trend analysis |
| **Maritime operators** | Route optimization, compliance, operational planning |

---

## 2. Gap Analysis — Why ORCA Is Needed

Based on documented gaps from INCOIS publications, CAG audit reports, and analysis of SAMUDRA, FFMA, Machli, and IMD services:

| Gap | Evidence | ORCA's Response |
|-----|----------|----------------|
| **No conversational interface** | All existing apps (SAMUDRA, FFMA, Machli) are menu-driven with static maps and pre-formatted bulletins | Multi-turn NL chat with context memory |
| **No multi-source correlation** | PFZ uses only SST + chlorophyll; IMD and INCOIS issue separate, disconnected bulletins | Multi-agent reasoning correlates SST + chlorophyll + wind + waves + tides + alerts |
| **No explainability** | CAG audit notes trust issues and no validated species-specific advisories; fishers distrust "black box" outputs | Every recommendation shows data provenance, rationale, and source timestamps |
| **Generic advisories only** | Advisories are per-sector/landing-center, not per-user trip plan | Personalized risk assessment for user's location, vessel, time window |
| **Batch-only data** | INCOIS PFZ/OSF are daily; no public real-time API exists | Near-real-time supplementary layer from Copernicus/NASA/NOAA between advisory cycles |
| **Limited regional language NLP** | Apps support static UI translations, but no conversational NLP in Malayalam, Tamil, Telugu etc. | Auto-detect language, respond conversationally in the same language |
| **No interactive geospatial chat** | Maps in SAMUDRA/Machli are visual overlays only — no "click a route and ask about risks" | Chat-linked map: draw routes, select areas, ask questions tied to map interactions |
| **Weak feedback loops** | CAG notes INCOIS couldn't validate species-specific advisories due to zero app feedback | Users can validate/correct recommendations, closing the data gap |

---

## 3. Novel Features — What No Existing Product Offers

> [!IMPORTANT]
> These are ORCA's differentiators. Every feature below is absent from SAMUDRA, FFMA, Machli, IMD portals, and known SIH solutions.

### 3.1 Conversational Marine Intelligence (Chat-First UX)
Multi-turn, context-aware NL chat over marine data. Not a search bar — a reasoning agent that remembers your location, vessel type, and previous questions.

### 3.2 Multi-Agent Reasoning Pipeline
Autonomous task decomposition: user asks one question → planner breaks it into sub-tasks → specialized agents (weather, ocean, safety, geofencing) execute in parallel → results are synthesized into one coherent, explained answer.

### 3.3 Near-Real-Time Global Data Layer
Continuously refreshed SST/chlorophyll/currents/tides from Copernicus Marine Toolbox, NASA Ocean Color (GEE), and NOAA APIs — **complementing** INCOIS's official daily advisories, not replacing them. Users get up-to-date context between advisory batch cycles.

### 3.4 Explainable Evidence Trails
Every recommendation carries:
- Which data sources were consulted (with timestamps)
- What thresholds triggered the recommendation (e.g., "Wind > 45 km/h, IMD fishermen warning active")
- Confidence level and caveats

### 3.5 Interactive Geospatial Chat
Map and chat are bidirectionally linked:
- Click a point on map → "What are conditions here?"
- Draw a route → "Show risk hotspots along this path"
- Chat response highlights relevant zones on map

### 3.6 Geofencing with Contextual Alerts
Proactive notifications when approaching EEZ boundaries, marine protected areas, restricted waters, or fishing ban zones — with **explanations** ("You are 5km from the India-Sri Lanka maritime boundary. Crossing is prohibited under...").

### 3.7 Regional Language Voice I/O
Beyond static UI translation: actual conversational voice input/output in Indian coastal languages (Tamil, Malayalam, Telugu, Kannada, Odia, Bengali, Marathi, Gujarati, Hindi) using open-source ASR + TTS.

### 3.8 Feedback-Driven Advisory Improvement
Users can mark recommendations as accurate/inaccurate with optional catch data, creating a **validation dataset** that addresses the exact feedback gap CAG identified in INCOIS's systems.

### 3.9 Multi-Source Data Fusion & Caching on Backblaze B2
All pulled global data (NetCDF, GeoTIFF, JSON) is cached on **Backblaze B2** (S3-compatible), enabling:
- Offline-capable cached responses
- Historical trend queries
- Reduced API call costs and latency

### 3.10 Route Optimization with Risk Overlay
Given origin, destination, and vessel constraints → compute safest route considering live weather, wave height, current direction, restricted zones, and time of day.

---

## 4. Tech Stack — Free & Open-Source

> [!TIP]
> Every tool below is free-tier or fully open-source. No paid licenses required.

### 4.1 Frontend

| Tool | Purpose | Cost |
|------|---------|------|
| **React 18 + Vite** | SPA framework + fast bundler | Free, OSS |
| **Leaflet.js + OpenStreetMap** | Interactive maps (no API key needed) | Free, OSS |
| **React-Leaflet** | React bindings for Leaflet | Free, OSS |
| **Chart.js / Recharts** | Data visualization (SST trends, wave charts) | Free, OSS |
| **Bootstrap 5** | Responsive CSS framework | Free, OSS |
| **Socket.IO Client** | Real-time WebSocket for chat + alerts | Free, OSS |
| **React-Markdown** | Render agent responses with formatting | Free, OSS |

### 4.2 Backend

| Tool | Purpose | Cost |
|------|---------|------|
| **Python 3.11+ / FastAPI** | Async API server with auto OpenAPI docs | Free, OSS |
| **Socket.IO (python-socketio)** | WebSocket for real-time chat + push alerts | Free, OSS |
| **Uvicorn** | ASGI server | Free, OSS |
| **Pydantic** | Request/response validation & typed schemas | Free, OSS |
| **APScheduler** | Cron-like scheduler for data pipeline jobs | Free, OSS |
| **httpx** | Async HTTP client for external API calls | Free, OSS |

### 4.3 AI / Agent Layer

| Tool | Purpose | Cost |
|------|---------|------|
| **LangChain + LangGraph** | Multi-agent orchestration with stateful graphs | Free, OSS |
| **Google Gemini API** | LLM backbone (free tier: 15 RPM, 1M tokens/day) | Free tier |
| **ChromaDB** | Local vector store for RAG over advisories/docs | Free, OSS |
| **Sentence-Transformers** | Embedding model for vector search | Free, OSS |

### 4.4 Data Pipeline & Storage

| Tool | Purpose | Cost |
|------|---------|------|
| **Backblaze B2** | S3-compatible object storage for cached EO data | **10 GB free**, S3 API |
| **boto3** | Python SDK to interact with Backblaze B2 via S3 API | Free, OSS |
| **xarray + netCDF4** | Read/process satellite NetCDF data | Free, OSS |
| **rasterio** | Read/process GeoTIFF raster data | Free, OSS |
| **PostgreSQL + PostGIS** | Spatial database for geofencing, boundaries, caching | Free, OSS |
| **Supabase** | Hosted Postgres with PostGIS (free tier: 500MB) | Free tier |

### 4.5 Geospatial

| Tool | Purpose | Cost |
|------|---------|------|
| **GeoPandas + Shapely** | Vector geometry operations, boundary checks | Free, OSS |
| **Turf.js** (frontend) | Client-side geospatial calculations | Free, OSS |
| **Natural Earth Data** | EEZ, country boundary, coastline shapefiles | Free, public domain |
| **OpenRouteService** | Route computation API (free tier: 2000 req/day) | Free tier |

### 4.6 NLP & Multilingual

| Tool | Purpose | Cost |
|------|---------|------|
| **AI4Bharat IndicTrans2** | Open-source translation for 22 Indian languages | Free, OSS |
| **Whisper (OpenAI)** | Speech-to-text for voice input | Free, OSS |
| **gTTS / Coqui TTS** | Text-to-speech for voice responses | Free, OSS |
| **langdetect / fastText** | Language detection | Free, OSS |

### 4.7 DevOps & Deployment

| Tool | Purpose | Cost |
|------|---------|------|
| **Vercel** | Frontend hosting | Free tier |
| **Render / Railway** | Backend hosting (Python) | Free tier |
| **GitHub Actions** | CI/CD pipeline | Free for public repos |
| **Docker + Docker Compose** | Local development containers | Free, OSS |

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│  ┌──────────────┐  ┌──────────────────┐  ┌─────────────────────┐   │
│  │  Chat Panel   │  │  Interactive Map  │  │  Dashboard/Charts  │   │
│  │  (React +     │  │  (Leaflet.js +   │  │  (Chart.js +       │   │
│  │   Socket.IO)  │  │   React-Leaflet) │  │   Recharts)        │   │
│  └──────┬───────┘  └────────┬─────────┘  └─────────┬───────────┘   │
│         │                   │                       │               │
│         └───────────────────┼───────────────────────┘               │
│                             │                                       │
│                    WebSocket + REST                                  │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                          │
│  ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌──────────────────────┐ │
│  │ /chat    │ │ /map      │ │ /alerts   │ │ /data              │ │
│  │ WebSocket│ │ REST      │ │ REST+WS   │ │ REST               │ │
│  └────┬─────┘ └─────┬─────┘ └─────┬─────┘ └──────────┬─────────┘ │
└───────┼─────────────┼─────────────┼────────────────────┼───────────┘
        │             │             │                    │
┌───────┼─────────────┼─────────────┼────────────────────┼───────────┐
│       │      AGENT ORCHESTRATOR (LangGraph)            │           │
│       ▼                                                │           │
│  ┌─────────┐    ┌───────────────────────────────────┐  │           │
│  │ PLANNER │───▶│      AGENT EXECUTION GRAPH        │  │           │
│  │ AGENT   │    │                                   │  │           │
│  └─────────┘    │  ┌─────────┐  ┌──────────────┐   │  │           │
│                 │  │ WEATHER │  │ OCEAN        │   │  │           │
│                 │  │ AGENT   │  │ ANALYTICS    │   │  │           │
│                 │  └────┬────┘  │ AGENT        │   │  │           │
│                 │       │       └──────┬───────┘   │  │           │
│                 │  ┌────┴────┐  ┌──────┴───────┐   │  │           │
│                 │  │ SAFETY  │  │ GEOSPATIAL   │   │  │           │
│                 │  │ & RISK  │  │ REASONING    │   │  │           │
│                 │  │ AGENT   │  │ AGENT        │   │  │           │
│                 │  └────┬────┘  └──────┬───────┘   │  │           │
│                 │       │              │           │  │           │
│                 │  ┌────┴──────────────┴────────┐  │  │           │
│                 │  │ EXPLAINER / RESPONSE AGENT │  │  │           │
│                 │  └───────────────────────────┘  │  │           │
│                 └───────────────────────────────────┘  │           │
│                                                        │           │
│  ┌──────────────┐  ┌────────────┐  ┌────────────────┐  │           │
│  │ NLP /        │  │ VECTOR     │  │ TRANSLATION    │  │           │
│  │ LANGUAGE     │  │ STORE      │  │ ENGINE         │  │           │
│  │ DETECTOR     │  │ (ChromaDB) │  │ (IndicTrans2)  │  │           │
│  └──────────────┘  └────────────┘  └────────────────┘  │           │
└────────────────────────────────────────────────────────┼───────────┘
                                                         │
┌────────────────────────────────────────────────────────┼───────────┐
│                    DATA LAYER                          │           │
│                                                        │           │
│  ┌──────────────────┐  ┌──────────────────────────┐    │           │
│  │  PostgreSQL +    │  │  Backblaze B2            │    │           │
│  │  PostGIS         │  │  (S3-Compatible)         │    │           │
│  │                  │  │                          │    │           │
│  │  • User sessions │  │  • Cached NetCDF/GeoTIFF │    │           │
│  │  • Geofence zones│  │  • Satellite imagery     │    │           │
│  │  • Feedback data │  │  • Advisory PDFs         │    │           │
│  │  • Alert history │  │  • Processed JSON layers │    │           │
│  └──────────────────┘  └──────────────────────────┘    │           │
│                                                        │           │
│  ┌─────────────────────────────────────────────────┐   │           │
│  │            DATA PIPELINE (APScheduler)          │   │           │
│  │                                                 │   │           │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────────┐  │   │           │
│  │  │Copernicus│ │ NASA GEE │ │ NOAA APIs      │  │   │           │
│  │  │Marine API│ │ Ocean    │ │ (Tides,Weather)│  │   │           │
│  │  └────┬─────┘ └────┬─────┘ └───────┬────────┘  │   │           │
│  │       │             │               │           │   │           │
│  │       ▼             ▼               ▼           │   │           │
│  │  ┌──────────────────────────────────────────┐   │   │           │
│  │  │  ETL: Ingest → Process → Store to B2    │   │   │           │
│  │  └──────────────────────────────────────────┘   │   │           │
│  └─────────────────────────────────────────────────┘   │           │
│                                                        │           │
│  ┌─────────────────────────────────────────────────┐   │           │
│  │       INCOIS / IMD ADVISORY LAYER               │   │           │
│  │       (Official daily bulletins — scraped or     │   │           │
│  │        parsed, stored as RAG documents)          │   │           │
│  └─────────────────────────────────────────────────┘   │           │
└────────────────────────────────────────────────────────────────────┘
```

### 5.1 Data Flow Summary

```
User Question (text/voice)
    │
    ▼
Language Detection → Translation to English (if needed)
    │
    ▼
Planner Agent: Decompose into sub-tasks
    │
    ├──▶ Weather Agent → IMD alerts, NOAA forecast data
    ├──▶ Ocean Agent → SST, chlorophyll from B2 cache / Copernicus
    ├──▶ Safety Agent → Wave height, wind, cyclone risk scoring
    ├──▶ Geospatial Agent → Location context, boundary check, route analysis
    │
    ▼
Explainer Agent: Synthesize + cite evidence
    │
    ▼
Translation to user's language (if needed)
    │
    ▼
Response: Text + Map layers + Charts + Alerts
```

---

## 6. Backblaze B2 — Data Storage Strategy

### 6.1 Why Backblaze B2

- **10 GB free storage** — sufficient for hackathon demo data
- **S3-compatible API** — use standard `boto3` Python SDK
- **No egress fees for first 1 GB/day** — handles demo traffic
- Stores **processed EO data** so agents don't re-fetch from slow global APIs on every query

### 6.2 Bucket Structure

```
orca-marine-data/                          ← Single B2 bucket
│
├── satellite/
│   ├── sst/
│   │   ├── copernicus/
│   │   │   └── 2026-08-31_indian-ocean_sst.nc
│   │   └── nasa-modis/
│   │       └── 2026-08-31_chlor-sst.nc
│   ├── chlorophyll/
│   │   └── 2026-08-31_indian-ocean_chl.nc
│   └── currents/
│       └── 2026-08-31_indian-ocean_currents.nc
│
├── weather/
│   ├── imd/
│   │   └── 2026-08-31_marine-bulletin.json
│   └── noaa/
│       └── 2026-08-31_forecast.json
│
├── tides/
│   └── 2026-08-31_indian-coast_tides.json
│
├── advisories/
│   ├── pfz/
│   │   └── 2026-08-31_pfz-sectors.json
│   └── osf/
│       └── 2026-08-31_osf.json
│
├── boundaries/
│   ├── eez_india.geojson
│   ├── mpa_india.geojson
│   ├── fishing_ban_zones.geojson
│   └── international_boundaries.geojson
│
└── processed/
    ├── risk-maps/
    │   └── 2026-08-31_risk-composite.geojson
    └── trends/
        └── sst-7day-trend_sector-14.json
```

### 6.3 Access Pattern

```python
# Example: Backblaze B2 via boto3 S3 interface
import boto3

b2_client = boto3.client(
    's3',
    endpoint_url='https://s3.us-west-004.backblazeb2.com',
    aws_access_key_id=B2_KEY_ID,
    aws_secret_access_key=B2_APP_KEY
)

# Upload processed satellite data
b2_client.upload_file(
    'processed_sst.nc',
    'orca-marine-data',
    'satellite/sst/copernicus/2026-08-31_indian-ocean_sst.nc'
)

# Download for agent use
b2_client.download_file(
    'orca-marine-data',
    'satellite/sst/copernicus/2026-08-31_indian-ocean_sst.nc',
    'local_sst.nc'
)
```

---

## 7. Directory Structure

```
orca/
│
├── client/                          # ── ROLE 1: Frontend Engineer ──
│   ├── public/
│   │   ├── favicon.ico
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   │   ├── ChatWindow.jsx
│   │   │   │   ├── MessageBubble.jsx
│   │   │   │   ├── InputBar.jsx
│   │   │   │   └── VoiceButton.jsx
│   │   │   ├── Map/
│   │   │   │   ├── MapContainer.jsx
│   │   │   │   ├── LayerControl.jsx
│   │   │   │   ├── RouteDrawer.jsx
│   │   │   │   ├── GeofenceOverlay.jsx
│   │   │   │   └── MarkerPopup.jsx
│   │   │   ├── Dashboard/
│   │   │   │   ├── Dashboard.jsx
│   │   │   │   ├── WeatherCard.jsx
│   │   │   │   ├── OceanCard.jsx
│   │   │   │   ├── AlertBanner.jsx
│   │   │   │   └── TrendChart.jsx
│   │   │   └── common/
│   │   │       ├── Navbar.jsx
│   │   │       ├── Sidebar.jsx
│   │   │       ├── Loader.jsx
│   │   │       └── ErrorBoundary.jsx
│   │   ├── hooks/
│   │   │   ├── useSocket.js
│   │   │   ├── useChat.js
│   │   │   ├── useMap.js
│   │   │   └── useGeolocation.js
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   ├── socket.js
│   │   │   └── mapLayers.js
│   │   ├── styles/
│   │   │   ├── index.css
│   │   │   ├── chat.css
│   │   │   ├── map.css
│   │   │   └── dashboard.css
│   │   ├── utils/
│   │   │   ├── formatters.js
│   │   │   └── constants.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── server/                          # ── ROLE 2: Backend Engineer ──
│   ├── src/
│   │   ├── routes/
│   │   │   ├── chat.py
│   │   │   ├── map_data.py
│   │   │   ├── alerts.py
│   │   │   ├── feedback.py
│   │   │   └── health.py
│   │   ├── controllers/
│   │   │   ├── chat_controller.py
│   │   │   ├── map_controller.py
│   │   │   ├── alert_controller.py
│   │   │   └── feedback_controller.py
│   │   ├── middleware/
│   │   │   ├── rate_limiter.py
│   │   │   ├── cors.py
│   │   │   └── error_handler.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── session.py
│   │   │   ├── feedback.py
│   │   │   └── alert.py
│   │   ├── services/
│   │   │   ├── session_manager.py
│   │   │   └── notification_service.py
│   │   ├── config/
│   │   │   ├── settings.py
│   │   │   ├── database.py
│   │   │   └── backblaze.py
│   │   ├── websocket/
│   │   │   ├── socket_manager.py
│   │   │   └── events.py
│   │   └── app.py
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── agents/                          # ── ROLE 3: AI Agent Engineer ──
│   ├── orchestrator/
│   │   ├── graph.py                 # LangGraph state machine
│   │   ├── state.py                 # Shared agent state schema
│   │   └── router.py               # Intent classification + routing
│   ├── planner/
│   │   ├── planner_agent.py
│   │   └── task_decomposer.py
│   ├── agents/
│   │   ├── weather_agent.py
│   │   ├── ocean_agent.py
│   │   ├── safety_agent.py
│   │   ├── geospatial_agent.py
│   │   └── explainer_agent.py
│   ├── tools/
│   │   ├── weather_tools.py         # IMD/NOAA API wrappers
│   │   ├── ocean_tools.py           # Copernicus/NASA API wrappers
│   │   ├── geofence_tools.py        # Boundary check tools
│   │   ├── b2_tools.py              # Backblaze data retrieval
│   │   └── search_tools.py          # Vector search over advisories
│   ├── prompts/
│   │   ├── system_prompts.py
│   │   ├── planner_prompt.py
│   │   └── explainer_prompt.py
│   ├── memory/
│   │   ├── conversation_memory.py
│   │   └── context_store.py
│   ├── requirements.txt
│   └── __init__.py
│
├── pipeline/                        # ── ROLE 4: Data Pipeline Engineer ──
│   ├── ingestion/
│   │   ├── copernicus_ingestor.py
│   │   ├── nasa_gee_ingestor.py
│   │   ├── noaa_ingestor.py
│   │   ├── incois_scraper.py
│   │   └── imd_scraper.py
│   ├── processors/
│   │   ├── netcdf_processor.py
│   │   ├── geotiff_processor.py
│   │   ├── json_normalizer.py
│   │   └── advisory_parser.py
│   ├── storage/
│   │   ├── b2_uploader.py
│   │   ├── db_writer.py
│   │   └── vector_indexer.py
│   ├── schedulers/
│   │   ├── cron_config.py
│   │   └── pipeline_runner.py
│   ├── requirements.txt
│   └── __init__.py
│
├── geo/                             # ── ROLE 5: Geospatial Engineer ──
│   ├── services/
│   │   ├── boundary_service.py      # EEZ, MPA, restricted zone checks
│   │   ├── geofence_service.py      # Real-time geofence monitoring
│   │   ├── route_service.py         # Route optimization + risk overlay
│   │   └── spatial_query_service.py # Point/area queries against layers
│   ├── layers/
│   │   ├── layer_manager.py         # Serve GeoJSON layers for map
│   │   ├── sst_layer.py
│   │   ├── chlorophyll_layer.py
│   │   └── risk_layer.py
│   ├── boundaries/
│   │   ├── eez_india.geojson        # Pre-loaded boundary files
│   │   ├── mpa_india.geojson
│   │   └── fishing_sectors.geojson
│   ├── analysis/
│   │   ├── risk_calculator.py       # Composite risk scoring
│   │   ├── pfz_analyzer.py          # PFZ proximity + suitability
│   │   └── trend_analyzer.py        # Temporal trend detection
│   ├── requirements.txt
│   └── __init__.py
│
├── nlp/                             # ── ROLE 6: NLP & Multilingual Engineer ──
│   ├── detection/
│   │   ├── language_detector.py
│   │   └── intent_classifier.py
│   ├── translation/
│   │   ├── translator.py            # IndicTrans2 wrapper
│   │   └── marine_glossary.py       # Domain-specific term mappings
│   ├── voice/
│   │   ├── stt_engine.py            # Whisper-based speech-to-text
│   │   └── tts_engine.py            # gTTS/Coqui text-to-speech
│   ├── templates/
│   │   ├── response_templates.py    # Structured response formats
│   │   └── alert_templates.py       # Safety alert message templates
│   ├── rag/
│   │   ├── document_loader.py       # Load advisories into ChromaDB
│   │   ├── embedder.py              # Sentence-transformer embeddings
│   │   └── retriever.py             # Semantic search over advisories
│   ├── requirements.txt
│   └── __init__.py
│
├── shared/                          # ── SHARED CONTRACTS (all roles) ──
│   ├── schemas/
│   │   ├── chat_schema.py           # Message, Response, Session types
│   │   ├── marine_schema.py         # SST, Chlorophyll, Weather types
│   │   ├── geo_schema.py            # GeoJSON, BoundingBox, Route types
│   │   └── alert_schema.py          # Alert, Risk, Geofence types
│   ├── constants/
│   │   ├── data_sources.py          # API endpoints, bucket paths
│   │   ├── thresholds.py            # Safety thresholds (wind, wave etc.)
│   │   └── languages.py             # Supported language codes
│   └── utils/
│       ├── date_utils.py
│       ├── geo_utils.py
│       └── format_utils.py
│
├── tests/                           # ── Tests (each role adds theirs) ──
│   ├── test_agents/
│   ├── test_pipeline/
│   ├── test_geo/
│   ├── test_nlp/
│   └── test_server/
│
├── docs/                            # ── Documentation ──
│   ├── API.md
│   ├── ARCHITECTURE.md
│   └── DATA_SOURCES.md
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── Makefile                         # Common commands (setup, run, test)
```

---

## 8. Project Bootstrap — Getting Started

### 8.1 Prerequisites

```
- Python 3.11+
- Node.js 18+ & npm
- PostgreSQL 15+ with PostGIS extension
- Docker & Docker Compose (optional but recommended)
- Git
```

### 8.2 Environment Setup

```bash
# 1. Clone the repo
git clone https://github.com/<your-team>/orca.git
cd orca

# 2. Copy environment template
cp .env.example .env
# Fill in:
#   GEMINI_API_KEY=<your-free-gemini-key>
#   B2_KEY_ID=<backblaze-key-id>
#   B2_APP_KEY=<backblaze-app-key>
#   B2_BUCKET_NAME=orca-marine-data
#   B2_ENDPOINT=https://s3.us-west-004.backblazeb2.com
#   DATABASE_URL=postgresql://user:pass@localhost:5432/orca
#   COPERNICUS_USER=<copernicus-username>
#   COPERNICUS_PASS=<copernicus-password>

# 3. Backend setup
cd server
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 4. Agent layer setup
cd ../agents
pip install -r requirements.txt

# 5. Pipeline setup
cd ../pipeline
pip install -r requirements.txt

# 6. Geo setup
cd ../geo
pip install -r requirements.txt

# 7. NLP setup
cd ../nlp
pip install -r requirements.txt

# 8. Frontend setup
cd ../client
npm install

# 9. Database setup
psql -U postgres -c "CREATE DATABASE orca;"
psql -U postgres -d orca -c "CREATE EXTENSION postgis;"

# 10. Seed boundary data
cd ../geo
python -c "from services.boundary_service import seed_boundaries; seed_boundaries()"
```

### 8.3 Running Locally

```bash
# Terminal 1: Backend server
cd server
uvicorn src.app:app --reload --port 8000

# Terminal 2: Frontend dev server
cd client
npm run dev                    # → http://localhost:5173

# Terminal 3: Data pipeline (one-time seed or scheduled)
cd pipeline
python -m schedulers.pipeline_runner --once
```

### 8.4 Docker Compose (Full Stack)

```yaml
# docker-compose.yml
version: '3.8'
services:
  db:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_DB: orca
      POSTGRES_USER: orca
      POSTGRES_PASSWORD: orca_dev
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  server:
    build: ./server
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [db]
    volumes: ["./agents:/app/agents", "./geo:/app/geo", "./nlp:/app/nlp", "./shared:/app/shared"]

  client:
    build: ./client
    ports: ["5173:5173"]
    depends_on: [server]

volumes:
  pgdata:
```

---

## 9. Team Roles & Task Breakdown (6 Members × 8–10 Chunks)

> [!IMPORTANT]
> **Independence Principle**: Each role owns a clearly bounded module. Roles communicate through **shared schemas** (`shared/schemas/`) and **API contracts** (`server/src/routes/`). No role needs to edit another role's directory. This prevents merge conflicts and lets all 6 members work in parallel.

---

### ROLE 1 — Frontend & UI Engineer
**Owns:** `client/` directory
**Depends on:** Backend WebSocket + REST API contracts (defined in `shared/schemas/`)

| # | Task Chunk | Description | Output |
|---|-----------|-------------|--------|
| 1 | **Project scaffold** | Initialize React + Vite, install Bootstrap 5, Leaflet, Socket.IO client, Chart.js. Configure `vite.config.js` with proxy to backend. | Working `npm run dev` with blank app |
| 2 | **Design system & layout** | Build `Navbar`, `Sidebar`, responsive split-panel layout (chat left, map right). Dark ocean theme with Bootstrap variables. | `index.css`, `Navbar.jsx`, `Sidebar.jsx`, layout shell |
| 3 | **Chat window** | `ChatWindow.jsx` with message list, auto-scroll, message types (user, agent, system alert, map-action). Markdown rendering for agent responses. | Functional chat UI (mock data) |
| 4 | **Chat input bar + voice** | `InputBar.jsx` with text input, send button, `VoiceButton.jsx` for mic recording (MediaRecorder API → send WAV to backend). | Text and voice input working |
| 5 | **Interactive map** | `MapContainer.jsx` with Leaflet + OpenStreetMap. Layer toggler for SST, chlorophyll, risk, PFZ, boundaries. Click-to-query (click point → send coords to chat). | Map with toggleable layers |
| 6 | **Route drawer** | `RouteDrawer.jsx` using Leaflet.Draw plugin — user draws origin/destination on map → route sent to backend for risk analysis. | Draw route → get risk overlay |
| 7 | **Geofence overlay** | `GeofenceOverlay.jsx` — render EEZ, MPA, fishing ban polygons from GeoJSON. Color-coded by type. Popup on click showing zone info. | Boundary polygons on map |
| 8 | **Dashboard cards** | `WeatherCard`, `OceanCard`, `AlertBanner` — display current conditions (wind, waves, SST, alerts) from backend `/data` endpoint. | Dashboard panel with live data |
| 9 | **Trend charts** | `TrendChart.jsx` — Chart.js line/area charts for SST, chlorophyll, wave height time-series. Embedded in chat when agent returns trend data. | Inline charts in chat + dashboard |
| 10 | **Socket.IO integration** | Wire up `useSocket` hook for real-time chat messages and push alerts. Handle connection states, reconnection, and typing indicators. | End-to-end real-time chat working |

---

### ROLE 2 — Backend & API Engineer
**Owns:** `server/` directory
**Depends on:** Shared schemas, called by Frontend and Agent layer

| # | Task Chunk | Description | Output |
|---|-----------|-------------|--------|
| 1 | **FastAPI scaffold** | Set up FastAPI app with CORS, error handling middleware, health endpoint, Uvicorn config, `.env` loading with Pydantic Settings. | `app.py` running at `:8000` |
| 2 | **Database models** | SQLAlchemy + PostGIS models: `User` (optional), `Session` (chat context), `Feedback`, `Alert`, `CachedData`. Alembic migrations. | DB schema + migration scripts |
| 3 | **WebSocket chat endpoint** | Socket.IO server: `/chat` namespace. Receive user messages → forward to agent orchestrator → stream agent response back. Handle sessions. | `ws://localhost:8000/chat` working |
| 4 | **REST: Map data endpoints** | `GET /api/map/layers/{layer_type}` — serve GeoJSON for SST, chlorophyll, risk, boundaries from B2 cache or geo module. | Map data API tested with Postman |
| 5 | **REST: Alert endpoints** | `GET /api/alerts?lat=&lon=` — return active alerts for location. `POST /api/alerts/subscribe` — register for push alerts. | Alert query + subscription API |
| 6 | **REST: Data endpoints** | `GET /api/data/current?lat=&lon=` — return current SST, chlorophyll, wind, wave, tide for a point. Pulls from B2 cache. | Current conditions API |
| 7 | **REST: Feedback endpoint** | `POST /api/feedback` — store user validation (accurate/inaccurate, optional catch data). Links to session + recommendation. | Feedback storage working |
| 8 | **Backblaze B2 config** | `config/backblaze.py` — boto3 client singleton, helper functions: `upload_to_b2()`, `download_from_b2()`, `list_bucket()`, `get_signed_url()`. | B2 integration tested |
| 9 | **Session management** | Track multi-turn conversation state: user location, vessel type, language, last query context. Store in Postgres, pass to agents. | Session persistence across turns |
| 10 | **Rate limiting & error handling** | Rate limiter middleware (slowapi), structured error responses, request logging, graceful handling of external API failures. | Production-ready error handling |

---

### ROLE 3 — AI Agent Orchestration Engineer
**Owns:** `agents/` directory
**Depends on:** Tools (weather_tools, ocean_tools, etc.), shared schemas, called by Backend

| # | Task Chunk | Description | Output |
|---|-----------|-------------|--------|
| 1 | **LangGraph state machine** | Define the agent execution graph in `graph.py`: nodes for planner, weather, ocean, safety, geospatial, explainer. Edges based on task plan. State schema in `state.py`. | Working LangGraph with mock agents |
| 2 | **Planner agent** | Receives user query + context → classifies intent → decomposes into sub-tasks (which agents to call, in what order, with what params). Uses Gemini. | Planner outputting valid task plans |
| 3 | **Weather agent** | Queries IMD (via scraper) + NOAA APIs for wind, rain, cyclone, lightning data. Returns structured `WeatherReport` with risk flags. | Weather agent returning real data |
| 4 | **Ocean analytics agent** | Queries SST, chlorophyll, currents from B2 cache (Copernicus/NASA processed data). Determines PFZ proximity, productivity trends. | Ocean data retrieval + analysis |
| 5 | **Safety & risk agent** | Combines weather + ocean + advisory data → computes composite safety score. Applies thresholds from `shared/constants/thresholds.py`. Flags: safe / caution / danger. | Risk scoring with evidence |
| 6 | **Geospatial reasoning agent** | Uses geo module tools for boundary checks, nearest-PFZ calculations, route risk evaluation. Adds spatial context to every response. | Spatial reasoning integrated |
| 7 | **Explainer / response agent** | Takes all agent outputs → synthesizes a coherent, human-readable response. Cites sources, shows evidence, adds caveats. Formats for chat + map actions. | Explained, cited responses |
| 8 | **Tool definitions** | Implement LangChain Tool wrappers for each external capability: `get_weather()`, `get_sst()`, `check_boundary()`, `search_advisories()`, `get_from_b2()`. | All tools callable by agents |
| 9 | **Conversation memory** | Integrate LangGraph checkpointer for multi-turn context. Retrieve/update session state (user location, vessel, language, past queries). | Multi-turn conversations working |
| 10 | **Prompt engineering** | Craft and iterate system prompts for each agent. Include domain knowledge (safety thresholds, PFZ interpretation, advisory sources). Test with diverse queries. | Optimized prompt library |

---

### ROLE 4 — Data Pipeline & Storage Engineer
**Owns:** `pipeline/` directory + Backblaze B2 bucket management
**Depends on:** B2 config from Backend, shared schemas

| # | Task Chunk | Description | Output |
|---|-----------|-------------|--------|
| 1 | **Backblaze B2 bucket setup** | Create `orca-marine-data` bucket on B2 console. Generate application key. Configure lifecycle rules (auto-delete data >30 days old). Document access in `.env.example`. | B2 bucket ready, credentials documented |
| 2 | **Copernicus Marine ingestor** | Use `copernicusmarine` Python toolbox to download daily Indian Ocean SST, chlorophyll, currents. Subset by lat/lon bounding box. Save to NetCDF → upload to B2. | Daily Copernicus data in B2 |
| 3 | **NASA GEE ingestor** | Use Google Earth Engine Python API to pull MODIS-Aqua L3 chlorophyll-a and SST. Export as GeoTIFF → process → upload to B2. | Daily NASA data in B2 |
| 4 | **NOAA ingestor** | Hit NOAA CO-OPS API for tides/water levels, NOAA weather API for marine forecasts. Store as structured JSON in B2. | Tides + weather JSON in B2 |
| 5 | **INCOIS advisory scraper** | Parse INCOIS PFZ/OSF web pages (HTML/PDF). Extract sector-wise advisory data → normalize to JSON → upload to B2 + index in ChromaDB for RAG. | Daily INCOIS advisories in B2 + vector store |
| 6 | **IMD bulletin scraper** | Parse IMD Mausam marine weather bulletins, fishermen warnings. Extract structured alerts → JSON → B2 + vector store. | IMD alerts in B2 + vector store |
| 7 | **NetCDF/GeoTIFF processor** | `netcdf_processor.py` and `geotiff_processor.py` — read raw EO files with xarray/rasterio, extract values for Indian Ocean region, convert to GeoJSON tiles for map display. | Processed GeoJSON tiles in B2 |
| 8 | **Data freshness tracker** | Track `last_updated` timestamp per data source in Postgres. Expose `GET /api/data/freshness` so agents know how current each dataset is. Include timestamps in responses. | Freshness metadata available |
| 9 | **Scheduler setup** | Configure APScheduler cron jobs: Copernicus (every 6h), NASA (daily), NOAA (every 3h), INCOIS (every 12h), IMD (every 6h). Run as background tasks in server. | Automated data refresh pipeline |
| 10 | **Vector indexing** | When new advisories/bulletins are ingested, chunk text, generate embeddings (sentence-transformers), upsert into ChromaDB. Maintain source metadata for citations. | RAG index auto-updated with new data |

---

### ROLE 5 — Geospatial & Map Services Engineer
**Owns:** `geo/` directory + boundary data
**Depends on:** PostGIS database, B2 cached data, shared schemas

| # | Task Chunk | Description | Output |
|---|-----------|-------------|--------|
| 1 | **Boundary data setup** | Download and clean EEZ, MPA, fishing sector, international boundary GeoJSON from Natural Earth / government sources. Load into PostGIS. | Boundary geometries in PostGIS |
| 2 | **Boundary check service** | `boundary_service.py` — given `(lat, lon)`, return which zones the point falls in (EEZ, MPA, restricted, fishing sector). Uses PostGIS `ST_Contains`. | Point-in-polygon boundary API |
| 3 | **Geofence monitoring** | `geofence_service.py` — given user's current position + heading, check proximity to all boundary types. Return distance + direction to nearest boundary + alert type. | Geofence proximity alerts |
| 4 | **Nearest PFZ calculator** | Given user location + today's PFZ data (from B2), find nearest PFZ zones. Return distance, direction, bearing, estimated travel time. | PFZ proximity queries working |
| 5 | **Route risk analysis** | `route_service.py` — given polyline route, sample points along route, query weather/wave/current conditions at each point, identify risk hotspots. Return annotated route GeoJSON. | Route with risk overlay |
| 6 | **SST/Chlorophyll layer service** | Read processed GeoJSON tiles from B2, serve as API response for map overlays. Support bbox filtering and zoom-level simplification. | Map-ready SST + chlorophyll layers |
| 7 | **Composite risk layer** | Combine wind, wave, current, alert data into a single risk score grid. Output as GeoJSON heatmap for map display. Update with each data refresh. | Visual risk heatmap layer |
| 8 | **Spatial query service** | `spatial_query_service.py` — given a bounding box or polygon, aggregate all available data (SST, chlorophyll, wind, alerts) for that area. Used by agents for area-based questions. | Area-based data aggregation |
| 9 | **Trend analysis** | `trend_analyzer.py` — query B2 historical data for a location/sector. Compute 7-day/30-day SST, chlorophyll trends. Detect anomalies (marine heatwave, bloom). | Temporal trend detection |
| 10 | **GeoJSON optimization** | Simplify geometries for fast frontend rendering (Douglas-Peucker). Pre-compute zoom-level tiles. Cache frequently requested layers in Postgres. | Performant map layer delivery |

---

### ROLE 6 — NLP, Multilingual & RAG Engineer
**Owns:** `nlp/` directory
**Depends on:** ChromaDB vector store (populated by Pipeline), shared schemas, called by Agent layer

| # | Task Chunk | Description | Output |
|---|-----------|-------------|--------|
| 1 | **Language detection** | `language_detector.py` — auto-detect input language using fastText/langdetect. Support: Tamil, Malayalam, Telugu, Kannada, Odia, Bengali, Marathi, Gujarati, Hindi, English. | Accurate language detection |
| 2 | **Translation engine** | `translator.py` — wrap AI4Bharat IndicTrans2 for bidirectional translation (regional ↔ English). Fallback to Google Translate API (free tier) if model unavailable. | Translation pipeline working |
| 3 | **Marine glossary** | `marine_glossary.py` — domain-specific term mappings (PFZ, SST, chlorophyll, tidal bore, etc.) in all supported languages. Ensures technical terms translate correctly. | Glossary with 200+ terms |
| 4 | **Intent classifier** | `intent_classifier.py` — classify user queries into categories: safety_check, pfz_query, weather_query, route_planning, boundary_check, trend_analysis, general_info. Feed to planner agent. | Intent classification with >90% accuracy on test set |
| 5 | **Speech-to-text** | `stt_engine.py` — OpenAI Whisper (small/medium model) for transcribing voice input. Support Hindi + English reliably; best-effort for other Indian languages. | Voice-to-text pipeline |
| 6 | **Text-to-speech** | `tts_engine.py` — gTTS or Coqui TTS to generate audio responses. Auto-select language/voice based on detected user language. Return audio file URL. | Audio responses in regional languages |
| 7 | **RAG: Document loader** | `document_loader.py` — load INCOIS advisories, IMD bulletins, policy documents into ChromaDB. Chunk intelligently (by advisory section, not fixed-size). Add source metadata. | Advisory documents indexed |
| 8 | **RAG: Semantic search** | `retriever.py` — given a query, retrieve top-k relevant advisory chunks from ChromaDB. Return with source citation (document name, date, section). | Relevant advisory retrieval |
| 9 | **Response templates** | `response_templates.py` — structured templates for safety alerts, PFZ recommendations, weather summaries, route advisories. Ensure consistent, clear formatting across languages. | Template library for all response types |
| 10 | **Explainability formatting** | Format evidence trails: "Sources consulted: [list]. Key factors: [bullets]. Confidence: [high/medium/low]. Caveats: [list]." Translate entire evidence block to user's language. | Explained, cited, translated responses |

---

### 9.7 Detailed Task Specifications & Agent Implementation Guide by Role

> [!TIP]
> **AI AGENT EXECUTION PROTOCOL**:
> When an AI Agent or developer is tasked to implement any feature/chunk:
> 1. Lookup the target `[CHUNK_ID]` (e.g., `[CHUNK_ID: R2-C03]`).
> 2. Check **Prerequisites** to verify dependent modules exist.
> 3. Read **Target Files**, **Inputs**, **Outputs**, and **Implementation Steps**.
> 4. Generate/modify code strictly adhering to the specified schemas in `shared/schemas/`.
> 5. Validate the completed chunk against the **Acceptance Criteria**.

---

#### 9.7.1 ROLE 1: Frontend & UI Engineer (`client/`)

##### [CHUNK_ID: R1-C01] Project Scaffold & Dependencies
- **Role**: Role 1 (Frontend & UI Engineer)
- **Target Files**: `client/package.json`, `client/vite.config.js`, `client/src/main.jsx`, `client/src/index.css`
- **Prerequisites**: None
- **Inputs**: None
- **Outputs**: Initialized React 18 SPA with Vite bundler, Bootstrap 5, Leaflet, and API proxy config
- **Implementation Steps**:
  1. Initialize Vite React template: `npm create vite@latest client -- --template react`.
  2. Install UI & Map packages: `npm install bootstrap leaflet react-leaflet leaflet-draw socket.io-client chart.js react-chartjs-2 react-markdown lucide-react`.
  3. Configure `vite.config.js` proxy: map `/api` -> `http://localhost:8000` and `/ws` -> `ws://localhost:8000`.
  4. Import Bootstrap CSS (`bootstrap/dist/css/bootstrap.min.css`) and Leaflet CSS (`leaflet/dist/leaflet.css`) into `main.jsx`.
- **Acceptance Criteria**:
  - [ ] Running `npm run dev` starts dev server at `http://localhost:5173`.
  - [ ] Vite proxy routes backend API calls without CORS errors.

##### [CHUNK_ID: R1-C02] Design System & Split Layout
- **Role**: Role 1 (Frontend & UI Engineer)
- **Target Files**: `client/src/styles/index.css`, `client/src/components/common/Navbar.jsx`, `client/src/App.jsx`
- **Prerequisites**: `[R1-C01]`
- **Inputs**: Data freshness metadata from backend `/api/data/freshness`
- **Outputs**: Responsive dark ocean theme layout with 40/60 split container
- **Implementation Steps**:
  1. Setup dark ocean CSS custom properties in `index.css`: `--bg-dark: #0a192f`, `--bg-card: #172a45`, `--accent-teal: #64ffda`, `--alert-red: #ff6b6b`.
  2. Build `Navbar.jsx` containing ORCA branding, active dataset freshness pill badge, and language selector dropdown (`en`, `hi`, `ta`, `ml`, `te`, `kn`, `or`, `bn`, `mr`, `gu`).
  3. Construct split panel layout in `App.jsx`: Left column (40% width) for Chat/Dashboard, Right column (60% width) for MapContainer.
  4. Add responsive toggle button for mobile screens to switch between Chat and Map views.
- **Acceptance Criteria**:
  - [ ] Layout displays dark oceanic palette correctly across desktop and mobile screen sizes.
  - [ ] Language selection updates active UI language state.

##### [CHUNK_ID: R1-C03] Interactive Chat Window
- **Role**: Role 1 (Frontend & UI Engineer)
- **Target Files**: `client/src/components/Chat/ChatWindow.jsx`, `client/src/components/Chat/MessageBubble.jsx`
- **Prerequisites**: `[R1-C02]`
- **Inputs**: Array of `ChatMessage` objects from state/WebSocket
- **Outputs**: Multi-turn scrolling chat interface with markdown parsing and action buttons
- **Implementation Steps**:
  1. Build `MessageBubble.jsx` styling user queries (right aligned, teal accent) vs agent responses (left aligned, card background) vs system alerts (red outline).
  2. Integrate `react-markdown` inside `MessageBubble` to format response text, bullet points, data tables, and evidence sections.
  3. Implement auto-scroll hook using `useRef` to snap chat viewport to bottom when new messages arrive.
  4. Add interactive inline action buttons on agent messages (e.g. "Focus Map Zone", "Show SST Graph").
- **Acceptance Criteria**:
  - [ ] Markdown formatting, tables, and system alerts render cleanly inside bubbles.
  - [ ] Chat window automatically scrolls down when streaming tokens arrive.

##### [CHUNK_ID: R1-C04] Multi-Modal Input & Voice Controller
- **Role**: Role 1 (Frontend & UI Engineer)
- **Target Files**: `client/src/components/Chat/InputBar.jsx`, `client/src/components/Chat/VoiceButton.jsx`
- **Prerequisites**: `[R1-C03]`
- **Inputs**: User keyboard input, HTML5 Microphone Audio Stream
- **Outputs**: Text query submission and recorded audio base64 payload
- **Implementation Steps**:
  1. Build `InputBar.jsx` with text input, send button, prompt shortcut pills ("Is it safe tomorrow?", "Nearest PFZ"), and Enter key listener.
  2. Build `VoiceButton.jsx` using HTML5 `navigator.mediaDevices.getUserMedia()` and `MediaRecorder`.
  3. On mic button hold/toggle: record audio chunks into `Blob` (`audio/webm` or `audio/wav`).
  4. On recording stop: convert audio Blob to base64 string or FormData and trigger backend speech transcription endpoint `/api/tts`.
- **Acceptance Criteria**:
  - [ ] Text submission dispatches query to socket/REST service.
  - [ ] Microphone recording captures audio blob and sends audio payload to server.

##### [CHUNK_ID: R1-C05] Core Map Container Component
- **Role**: Role 1 (Frontend & UI Engineer)
- **Target Files**: `client/src/components/Map/MapContainer.jsx`, `client/src/components/Map/LayerControl.jsx`
- **Prerequisites**: `[R1-C01]`
- **Inputs**: Selected map layers, user coordinates, GeoJSON layer payloads
- **Outputs**: Interactive Leaflet map instance centered on Indian coastal waters
- **Implementation Steps**:
  1. Initialize React-Leaflet `MapContainer` centered at `[13.0827, 80.2707]` (Indian East Coast) at zoom level 6.
  2. Add base map `TileLayer` (OpenStreetMap or CartoDB Dark Matter tile server).
  3. Build `LayerControl.jsx` rendering checkbox toggles for visual layers: SST Heatmap, Chlorophyll Raster, Composite Risk, PFZ Lines, Boundaries.
  4. Attach map click listener capturing clicked `(lat, lon)` and emitting a "Query this point" action to the chat input bar.
- **Acceptance Criteria**:
  - [ ] Map renders smoothly with dark tiles and zoom/pan controls.
  - [ ] Clicking any point on the map retrieves coordinate `[lat, lon]` for query submission.

##### [CHUNK_ID: R1-C06] Interactive Route Drawer Component
- **Role**: Role 1 (Frontend & UI Engineer)
- **Target Files**: `client/src/components/Map/RouteDrawer.jsx`
- **Prerequisites**: `[R1-C05]`
- **Inputs**: User click waypoints on map canvas
- **Outputs**: Drawn route polyline and safety risk overlay
- **Implementation Steps**:
  1. Integrate `leaflet-draw` plugin or custom click-to-waypoint polyline listener.
  2. Capture array of coordinate pairs: `[[lat1, lon1], [lat2, lon2], ...]`.
  3. Submit polyline coordinates to backend REST endpoint `/api/geo/route-risk`.
  4. Render returned polyline on map color-coded by safety status (Green = safe, Yellow = caution, Red = hazard).
- **Acceptance Criteria**:
  - [ ] Users can draw multi-segment routes on map.
  - [ ] Route is highlighted with risk colors after backend risk evaluation.

##### [CHUNK_ID: R1-C07] Geofence & Boundary Polygon Overlay
- **Role**: Role 1 (Frontend & UI Engineer)
- **Target Files**: `client/src/components/Map/GeofenceOverlay.jsx`
- **Prerequisites**: `[R1-C05]`
- **Inputs**: GeoJSON datasets from `/api/map/layers/boundaries`
- **Outputs**: Visual boundary polygon overlays with interactive info popups
- **Implementation Steps**:
  1. Fetch boundary GeoJSON objects (EEZ, Marine Protected Areas, Fishing Ban Zones).
  2. Style polygon paths: EEZ (dashed blue line), MPAs (light green fill), Fishing Ban Zones (red hatch fill).
  3. Bind click popups to polygons displaying boundary name, legal rules, and distance from current user position.
- **Acceptance Criteria**:
  - [ ] Boundary polygons render accurately over coastal waters.
  - [ ] Clicking a boundary polygon pops up zone details and restrictions.

##### [CHUNK_ID: R1-C08] Marine Conditions Dashboard Cards
- **Role**: Role 1 (Frontend & UI Engineer)
- **Target Files**: `client/src/components/Dashboard/Dashboard.jsx`, `WeatherCard.jsx`, `OceanCard.jsx`, `AlertBanner.jsx`
- **Prerequisites**: `[R1-C02]`
- **Inputs**: Real-time point conditions from `/api/data/current`
- **Outputs**: Dashboard panel displaying SST, Chlorophyll, Wind, Wave, Tide, and Alert metrics
- **Implementation Steps**:
  1. Build `WeatherCard.jsx` displaying wind speed (knots), wind direction arrow, wave height (m), and swell period.
  2. Build `OceanCard.jsx` displaying SST (°C), Chlorophyll-a (mg/m³), and tide prediction level.
  3. Build `AlertBanner.jsx` showing active IMD severe weather or cyclone alerts in red banner.
  4. Fetch data dynamically whenever user changes location or clicks a map coordinate.
- **Acceptance Criteria**:
  - [ ] Metrics update dynamically based on selected coordinates.
  - [ ] Active hazard alerts display prominently in red alert banner.

##### [CHUNK_ID: R1-C09] Environmental Trend Chart Component
- **Role**: Role 1 (Frontend & UI Engineer)
- **Target Files**: `client/src/components/Dashboard/TrendChart.jsx`
- **Prerequisites**: `[R1-C08]`
- **Inputs**: Time-series historical data array from backend
- **Outputs**: Interactive Chart.js line graphs for historical SST and Chlorophyll trends
- **Implementation Steps**:
  1. Integrate Chart.js `Line` component inside `TrendChart.jsx`.
  2. Map 7-day and 30-day historical time-series datasets onto chart X-axis (dates) and Y-axis (values).
  3. Add dataset toggle buttons (SST °C vs Chlorophyll mg/m³).
  4. Allow embedding trend charts directly inside chat response bubbles when requested by agent.
- **Acceptance Criteria**:
  - [ ] Historical trend lines plot accurately with hover tooltips.
  - [ ] Charts adapt responsively inside dashboard panel and chat bubbles.

##### [CHUNK_ID: R1-C10] Socket.IO Client Manager & Event Wiring
- **Role**: Role 1 (Frontend & UI Engineer)
- **Target Files**: `client/src/hooks/useSocket.js`, `client/src/services/socket.js`
- **Prerequisites**: `[R1-C03]`, `[R1-C05]`
- **Inputs**: Server WebSocket events (`chat_response`, `map_action`, `push_alert`)
- **Outputs**: Connected WebSocket client handling real-time chat streaming and map triggers
- **Implementation Steps**:
  1. Initialize Socket.IO connection manager to `ws://localhost:8000/chat`.
  2. Build `useSocket` hook managing session room subscription with `session_id`.
  3. Handle incoming `chat_response` tokens: append to active message state.
  4. Handle incoming `map_action` payload: trigger map pan/zoom, highlight zone polygon, or draw route overlay.
  5. Handle `push_alert` payload: display alert toast notification.
- **Acceptance Criteria**:
  - [ ] Real-time token streaming works without losing message state.
  - [ ] Agent map actions automatically trigger map pan/zoom and layer drawing.

---

#### 9.7.2 ROLE 2: Backend & API Engineer (`server/`)

##### [CHUNK_ID: R2-C01] FastAPI Application Scaffold & Environment
- **Role**: Role 2 (Backend & API Engineer)
- **Target Files**: `server/src/app.py`, `server/src/config/settings.py`, `server/requirements.txt`
- **Prerequisites**: None
- **Inputs**: Environment configuration (`.env`)
- **Outputs**: Operational FastAPI server with CORS, error handling middleware, and settings
- **Implementation Steps**:
  1. Create `requirements.txt` with `fastapi`, `uvicorn`, `pydantic-settings`, `python-socketio`, `sqlalchemy`, `psycopg2-binary`, `geoalchemy2`, `boto3`, `slowapi`, `httpx`.
  2. Setup `settings.py` loading `.env` variables (`DATABASE_URL`, `B2_KEY_ID`, `B2_APP_KEY`, `GEMINI_API_KEY`).
  3. Initialize FastAPI instance in `app.py` with OpenAPI documentation metadata.
  4. Add CORS middleware permitting `http://localhost:5173` with credentials.
  5. Add global error handler returning JSON errors (`{"status": "error", "message": "..."}`).
- **Acceptance Criteria**:
  - [ ] Server launches via `uvicorn src.app:app --reload` on port 8000.
  - [ ] OpenAPI docs accessible at `http://localhost:8000/docs`.

##### [CHUNK_ID: R2-C02] Database Schema & PostGIS Migrations
- **Role**: Role 2 (Backend & API Engineer)
- **Target Files**: `server/src/config/database.py`, `server/src/models/user.py`, `session.py`, `feedback.py`, `alert.py`
- **Prerequisites**: `[R2-C01]`
- **Inputs**: PostGIS database connection string
- **Outputs**: SQLAlchemy ORM models and database tables with spatial geometry support
- **Implementation Steps**:
  1. Setup SQLAlchemy async engine and sessionmaker in `database.py`.
  2. Create ORM models in `models/`:
     - `Session`: `session_id` (PK), `location` (Point), `language`, `vessel_type`, `created_at`.
     - `Feedback`: `id` (PK), `session_id`, `rating`, `is_accurate`, `catch_species`, `catch_qty_kg`, `created_at`.
     - `Alert`: `id` (PK), `hazard_type`, `geometry` (Polygon/Point), `risk_level`, `valid_until`.
  3. Setup Alembic migration config and execute initial table migrations.
- **Acceptance Criteria**:
  - [ ] PostgreSQL tables created with PostGIS spatial geometry column support.
  - [ ] Migration scripts run cleanly without schema conflicts.

##### [CHUNK_ID: R2-C03] WebSocket Server Engine (`socket_manager.py`)
- **Role**: Role 2 (Backend & API Engineer)
- **Target Files**: `server/src/websocket/socket_manager.py`, `server/src/websocket/events.py`
- **Prerequisites**: `[R2-C01]`
- **Inputs**: Client WebSocket messages (`user_message`)
- **Outputs**: Async Socket.IO server streaming agent response chunks
- **Implementation Steps**:
  1. Mount `python-socketio` AsyncServer onto FastAPI app with ASGI app wrapper.
  2. Handle `connect` and `disconnect` events, managing socket room join by `session_id`.
  3. Handle `user_message` event: extract query text, location, and session_id -> trigger LangGraph orchestrator asynchronously.
  4. Stream response tokens back to client using `sio.emit('chat_response', chunk, room=session_id)`.
- **Acceptance Criteria**:
  - [ ] WebSocket connections establish successfully on `/chat` namespace.
  - [ ] Server streams response chunks back to client room asynchronously.

##### [CHUNK_ID: R2-C04] Map Data REST Endpoints
- **Role**: Role 2 (Backend & API Engineer)
- **Target Files**: `server/src/routes/map_data.py`, `server/src/controllers/map_controller.py`
- **Prerequisites**: `[R2-C02]`
- **Inputs**: Map layer type, bounding box query params (`min_lat`, `max_lat`, `min_lon`, `max_lon`)
- **Outputs**: Filtered GeoJSON layer FeatureCollections for map overlay rendering
- **Implementation Steps**:
  1. Implement `GET /api/map/layers/{layer_type}` (`sst`, `chlorophyll`, `risk`, `pfz`, `boundaries`).
  2. Parse bounding box query parameters.
  3. Query PostGIS or fetch cached GeoJSON files from Backblaze B2 bucket storage.
  4. Add HTTP ETag and Cache-Control headers for client side response caching.
- **Acceptance Criteria**:
  - [ ] Endpoints return valid GeoJSON FeatureCollections matching bounding box.
  - [ ] Response headers include caching tags for fast repeat loads.

##### [CHUNK_ID: R2-C05] Active Hazard Alert Endpoints
- **Role**: Role 2 (Backend & API Engineer)
- **Target Files**: `server/src/routes/alerts.py`, `server/src/controllers/alert_controller.py`
- **Prerequisites**: `[R2-C02]`
- **Inputs**: User coordinates (`lat`, `lon`), alert push subscription token
- **Outputs**: Active hazard alerts list and alert push registration confirmation
- **Implementation Steps**:
  1. Implement `GET /api/alerts?lat=&lon=`: query active IMD warnings and high-wave alerts within 50km radius.
  2. Implement `POST /api/alerts/subscribe`: accept subscription payload (`session_id`, `push_token`, `location`, `radius_km`).
  3. Store push subscription in database table for automated background hazard broadcast.
- **Acceptance Criteria**:
  - [ ] `GET /api/alerts` returns active alerts within radius of location.
  - [ ] Push subscriptions save successfully to database.

##### [CHUNK_ID: R2-C06] Single-Point Current Data REST API
- **Role**: Role 2 (Backend & API Engineer)
- **Target Files**: `server/src/routes/data.py`, `server/src/controllers/data_controller.py`
- **Prerequisites**: `[R2-C01]`
- **Inputs**: Point coordinates (`lat`, `lon`)
- **Outputs**: `MarineConditions` JSON object containing SST, Chlorophyll, Wind, Wave, and Tide metrics
- **Implementation Steps**:
  1. Implement `GET /api/data/current?lat=&lon=`.
  2. Intersect requested `(lat, lon)` with latest processed NetCDF/JSON grid files stored in Backblaze B2 cache.
  3. Construct and return `MarineConditions` Pydantic model payload with dataset freshness timestamps.
- **Acceptance Criteria**:
  - [ ] Returns structured point metrics object containing SST, wind, wave, and tide values.
  - [ ] Response includes source dataset timestamp metadata.

##### [CHUNK_ID: R2-C07] User Feedback & Validation Endpoint
- **Role**: Role 2 (Backend & API Engineer)
- **Target Files**: `server/src/routes/feedback.py`, `server/src/controllers/feedback_controller.py`
- **Prerequisites**: `[R2-C02]`
- **Inputs**: `FeedbackCreate` JSON payload
- **Outputs**: Stored feedback record ID and success response
- **Implementation Steps**:
  1. Implement `POST /api/feedback` endpoint validating input against `FeedbackCreate` schema.
  2. Insert feedback record into PostgreSQL database table `feedback`.
  3. Log validation feedback metrics (rating, accuracy flag, caught species/quantity) for INCOIS advisory evaluation reporting.
- **Acceptance Criteria**:
  - [ ] Valid feedback requests save cleanly to PostgreSQL database.
  - [ ] Endpoint validates input schema and rejects invalid submissions.

##### [CHUNK_ID: R2-C08] Backblaze B2 S3 Client SDK Engine
- **Role**: Role 2 (Backend & API Engineer)
- **Target Files**: `server/src/config/backblaze.py`
- **Prerequisites**: `[R2-C01]`
- **Inputs**: B2 endpoint URL, B2 Key ID, B2 Application Key
- **Outputs**: Singleton `boto3` S3 client helper module for object storage operations
- **Implementation Steps**:
  1. Initialize `boto3.client('s3')` pointing to Backblaze endpoint `s3.us-west-004.backblazeb2.com`.
  2. Implement helper `download_b2_file(bucket_key, local_path)`.
  3. Implement helper `upload_b2_file(local_path, bucket_key)`.
  4. Implement helper `get_b2_json(bucket_key)` parsing JSON objects directly from B2 storage.
  5. Implement helper `get_presigned_url(bucket_key, expires_in=3600)`.
- **Acceptance Criteria**:
  - [ ] B2 client reads/writes files from Backblaze B2 bucket cleanly using S3 API.
  - [ ] Presigned URLs generate correctly for frontend media downloads.

##### [CHUNK_ID: R2-C09] Multi-Turn Session State Manager
- **Role**: Role 2 (Backend & API Engineer)
- **Target Files**: `server/src/services/session_manager.py`
- **Prerequisites**: `[R2-C02]`
- **Inputs**: `session_id`, session state delta
- **Outputs**: Persistent session state context object across multi-turn interactions
- **Implementation Steps**:
  1. Implement `get_session(session_id)` retrieving active context from DB (chat history, user location, vessel specs, language).
  2. Implement `update_session(session_id, delta)` saving updated state attributes.
  3. Add auto-cleanup logic for stale sessions older than 24 hours.
- **Acceptance Criteria**:
  - [ ] Multi-turn session state persists across REST and WebSocket calls.
  - [ ] Stale sessions expire cleanly.

##### [CHUNK_ID: R2-C10] Rate Limiter & System Health API
- **Role**: Role 2 (Backend & API Engineer)
- **Target Files**: `server/src/middleware/rate_limiter.py`, `server/src/routes/health.py`
- **Prerequisites**: `[R2-C01]`
- **Inputs**: Client HTTP requests
- **Outputs**: Rate-limited endpoints and system health status JSON
- **Implementation Steps**:
  1. Configure `slowapi` rate limiter middleware applying max 60 requests/minute per client IP.
  2. Implement `GET /api/health` checking: PostgreSQL database ping, Backblaze B2 bucket reachability, and Gemini API key validity.
  3. Return health summary JSON (`{"status": "healthy", "database": "up", "b2": "up", "gemini": "up"}`).
- **Acceptance Criteria**:
  - [ ] Rate limiter blocks excessive requests with HTTP 429 status code.
  - [ ] Health check returns component status report.

---

#### 9.7.3 ROLE 3: AI Agent Orchestration Engineer (`agents/`)

##### [CHUNK_ID: R3-C01] LangGraph State Machine Architecture
- **Role**: Role 3 (AI Agent Orchestration Engineer)
- **Target Files**: `agents/orchestrator/state.py`, `graph.py`
- **Prerequisites**: None
- **Inputs**: User prompt text, session context
- **Outputs**: Stateful multi-agent execution graph
- **Implementation Steps**:
  1. Define `AgentState` schema in `state.py`: `query`, `language`, `session_id`, `location`, `vessel_type`, `plan`, `weather_data`, `ocean_data`, `safety_data`, `geo_data`, `final_response`, `evidence_trail`.
  2. Define nodes in `graph.py`: `planner`, `weather_agent`, `ocean_agent`, `safety_agent`, `geospatial_agent`, `explainer`.
  3. Add conditional routing edges based on plan output and compile `StateGraph`.
- **Acceptance Criteria**:
  - [ ] LangGraph compiles without circular reference or syntax errors.
  - [ ] State passes seamlessly between graph nodes.

##### [CHUNK_ID: R3-C02] Intent Classifier & Task Planner Agent
- **Role**: Role 3 (AI Agent Orchestration Engineer)
- **Target Files**: `agents/planner/planner_agent.py`, `task_decomposer.py`
- **Prerequisites**: `[R3-C01]`
- **Inputs**: User query string, user location, vessel specs
- **Outputs**: Structured execution DAG specifying required specialist agents and parameters
- **Implementation Steps**:
  1. Prompt Gemini 1.5 Flash model with system prompt instructing task decomposition.
  2. Input user prompt + context.
  3. Output structured JSON task plan: `{"intent": "safety_check", "required_agents": ["weather", "ocean", "safety"], "subtasks": [...]}`.
- **Acceptance Criteria**:
  - [ ] Planner correctly decomposes complex queries into valid JSON plans.
  - [ ] Correctly identifies necessary specialist agents for diverse user prompts.

##### [CHUNK_ID: R3-C03] Weather Intelligence Specialist Agent
- **Role**: Role 3 (AI Agent Orchestration Engineer)
- **Target Files**: `agents/agents/weather_agent.py`
- **Prerequisites**: `[R3-C01]`
- **Inputs**: Location `[lat, lon]`, target forecast time window
- **Outputs**: Structured `WeatherReport` object in state
- **Implementation Steps**:
  1. Call weather tools: `get_imd_warnings(lat, lon)`, `get_noaa_wave_forecast(lat, lon)`.
  2. Extract wind speed (knots), wind direction, wave height (m), swell period, and active squall alerts.
  3. Save normalized `WeatherReport` to graph state.
- **Acceptance Criteria**:
  - [ ] Agent correctly retrieves and parses meteorological hazard metrics.
  - [ ] Populates `weather_data` node in state.

##### [CHUNK_ID: R3-C04] Ocean Analytics Specialist Agent
- **Role**: Role 3 (AI Agent Orchestration Engineer)
- **Target Files**: `agents/agents/ocean_agent.py`
- **Prerequisites**: `[R3-C01]`
- **Inputs**: Location `[lat, lon]`, bounding box
- **Outputs**: Structured `OceanReport` object in state
- **Implementation Steps**:
  1. Call ocean tools to query SST and Chlorophyll-a rasters from Backblaze B2 storage cache.
  2. Compute SST gradients, chlorophyll concentration averages, and PFZ suitability.
  3. Save normalized `OceanReport` to graph state.
- **Acceptance Criteria**:
  - [ ] Agent retrieves SST and Chlorophyll values for target location.
  - [ ] Evaluates thermal front and productivity indicators.

##### [CHUNK_ID: R3-C05] Safety & Risk Assessment Specialist Agent
- **Role**: Role 3 (AI Agent Orchestration Engineer)
- **Target Files**: `agents/agents/safety_agent.py`
- **Prerequisites**: `[R3-C03]`, `[R3-C04]`
- **Inputs**: `weather_data`, `ocean_data`, vessel specification
- **Outputs**: Composite safety assessment (`SAFE`, `CAUTION`, `DANGER`) with risk score
- **Implementation Steps**:
  1. Load safety threshold constants from `shared/constants/thresholds.py`.
  2. Evaluate wind, wave height, swell period, and active IMD warnings against boat size limit (e.g. 7m open boat vs 15m trawler).
  3. Compute composite risk score (0.0 to 1.0) and output status: `SAFE`, `CAUTION`, or `DANGER` with reasoning list.
- **Acceptance Criteria**:
  - [ ] Assigns accurate safety level based on weather thresholds and vessel size.
  - [ ] Generates explicit risk factor bullet points.

##### [CHUNK_ID: R3-C06] Geospatial Reasoning Specialist Agent
- **Role**: Role 3 (AI Agent Orchestration Engineer)
- **Target Files**: `agents/agents/geospatial_agent.py`
- **Prerequisites**: `[R3-C01]`
- **Inputs**: Coordinates, route polyline waypoints
- **Outputs**: Spatial boundary checks, nearest PFZ coordinates, map action payload
- **Implementation Steps**:
  1. Invoke geo tools: `check_boundaries(lat, lon)`, `find_nearest_pfz(lat, lon)`, `evaluate_route_risk(waypoints)`.
  2. Calculate distance to international maritime boundaries (IMBL) or restricted zones.
  3. Construct `MapAction` payload instructing frontend map UI to pan/zoom or draw risk layers.
- **Acceptance Criteria**:
  - [ ] Correctly identifies boundary proximity and nearest PFZ zones.
  - [ ] Generates valid `MapAction` payloads for frontend map execution.

##### [CHUNK_ID: R3-C07] Synthesis & Explainer Agent
- **Role**: Role 3 (AI Agent Orchestration Engineer)
- **Target Files**: `agents/agents/explainer_agent.py`
- **Prerequisites**: `[R3-C03]`, `[R3-C04]`, `[R3-C05]`, `[R3-C06]`
- **Inputs**: Aggregated outputs from all specialist agents
- **Outputs**: Final Markdown conversational response text with evidence citation section
- **Implementation Steps**:
  1. Combine state data from Weather, Ocean, Safety, and Geospatial agents.
  2. Prompt Gemini 1.5 model to synthesize findings into a clear, empathetic response.
  3. Format evidence block: "Data Sources Consulted: [list]. Dataset Timestamps: [...]. Key Factors: [...]. Confidence: High."
  4. Include disclaimers and source citations.
- **Acceptance Criteria**:
  - [ ] Synthesizes all agent outputs into a coherent conversational answer.
  - [ ] Includes clear evidence trail and data source timestamps.

##### [CHUNK_ID: R3-C08] Agent Tool Registry Module
- **Role**: Role 3 (AI Agent Orchestration Engineer)
- **Target Files**: `agents/tools/weather_tools.py`, `ocean_tools.py`, `geofence_tools.py`, `b2_tools.py`, `search_tools.py`
- **Prerequisites**: `[R3-C01]`
- **Inputs**: Tool invocation arguments
- **Outputs**: Executable `@tool` functions wrapping backend services and data lookups
- **Implementation Steps**:
  1. Create LangChain `@tool` functions wrapping REST client calls and database queries.
  2. Add Pydantic argument validation to every tool function.
  3. Add exception handling wrappers so tool failures return informative error strings without crashing the agent graph.
- **Acceptance Criteria**:
  - [ ] All tools execute cleanly when called by LangGraph agents.
  - [ ] Tool exceptions are caught gracefully.

##### [CHUNK_ID: R3-C09] Conversation Memory Checkpointer
- **Role**: Role 3 (AI Agent Orchestration Engineer)
- **Target Files**: `agents/memory/conversation_memory.py`, `context_store.py`
- **Prerequisites**: `[R3-C01]`
- **Inputs**: `session_id`, LangGraph state checkpoints
- **Outputs**: Persisted agent memory allowing multi-turn conversational context retention
- **Implementation Steps**:
  1. Configure `AsyncPostgresSaver` / `MemorySaver` checkpointer in LangGraph execution loop.
  2. Key graph state memory by `session_id`.
  3. Restore state on sub-sequent user chat turns to retain location, vessel, and query context.
- **Acceptance Criteria**:
  - [ ] Multi-turn chat retains context across turns (e.g. "What about tomorrow morning?").
  - [ ] State saves reliably to database memory store.

##### [CHUNK_ID: R3-C10] System Prompt Engineering & Safety Guardrails
- **Role**: Role 3 (AI Agent Orchestration Engineer)
- **Target Files**: `agents/prompts/system_prompts.py`, `planner_prompt.py`, `explainer_prompt.py`
- **Prerequisites**: `[R3-C02]`, `[R3-C07]`
- **Inputs**: Domain safety rules and guidelines
- **Outputs**: Optimized prompt templates with strict output structure and guardrails
- **Implementation Steps**:
  1. System prompt directives enforcing domain tone, safety emphasis, and structured markdown output.
  2. Inject safety guardrails prohibiting agents from giving binding legal advice on international border crossings or unverified navigation guarantees.
  3. Test prompt variations against edge-case queries to ensure safety guidelines are followed.
- **Acceptance Criteria**:
  - [ ] Agents consistently adhere to markdown formatting and safety guardrails.
  - [ ] Prompts handle ambiguous user queries safely.

---

#### 9.7.4 ROLE 4: Data Pipeline & Storage Engineer (`pipeline/`)

##### [CHUNK_ID: R4-C01] Backblaze B2 Infrastructure Configuration
- **Role**: Role 4 (Data Pipeline Engineer)
- **Target Files**: `pipeline/storage/b2_uploader.py`, `pipeline/config.py`
- **Prerequisites**: None
- **Inputs**: B2 API credentials
- **Outputs**: Configured Backblaze B2 storage bucket and directory layout
- **Implementation Steps**:
  1. Create B2 bucket `orca-marine-data` programmatically via script/SDK.
  2. Setup directory key structure: `satellite/sst/`, `satellite/chlorophyll/`, `weather/imd/`, `weather/noaa/`, `advisories/pfz/`, `boundaries/`.
  3. Apply lifecycle rule auto-deleting raw temporary staging files after 30 days.
- **Acceptance Criteria**:
  - [ ] B2 bucket directory hierarchy initialized.
  - [ ] Test file uploads/downloads succeed via `b2_uploader.py`.

##### [CHUNK_ID: R4-C02] Copernicus Marine Satellite Data Ingestor
- **Role**: Role 4 (Data Pipeline Engineer)
- **Target Files**: `pipeline/ingestion/copernicus_ingestor.py`
- **Prerequisites**: `[R4-C01]`
- **Inputs**: Copernicus Marine API credentials
- **Outputs**: Daily NetCDF files (SST, Chlorophyll, Ocean Currents) uploaded to Backblaze B2
- **Implementation Steps**:
  1. Write Python script using `copernicusmarine` SDK toolbox.
  2. Query daily global ocean dataset, subset bounding box to Indian Ocean (`5°N to 25°N`, `65°E to 95°E`).
  3. Download NetCDF file, compress, and upload to Backblaze B2 (`satellite/sst/copernicus/YYYY-MM-DD.nc`).
- **Acceptance Criteria**:
  - [ ] Downloads Indian Ocean NetCDF dataset automatically from Copernicus API.
  - [ ] Uploads compressed dataset to Backblaze B2.

##### [CHUNK_ID: R4-C03] NASA GEE MODIS Satellite Data Ingestor
- **Role**: Role 4 (Data Pipeline Engineer)
- **Target Files**: `pipeline/ingestion/nasa_gee_ingestor.py`
- **Prerequisites**: `[R4-C01]`
- **Inputs**: Google Earth Engine API credentials
- **Outputs**: MODIS-Aqua L3 Chlorophyll-a and SST GeoTIFF rasters in B2
- **Implementation Steps**:
  1. Authenticate GEE Python SDK (`ee.Initialize()`).
  2. Query dataset `ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua_L3SMI")`.
  3. Select latest daily `chlor_a` and `sst` bands, clip to Indian EEZ bounding box, export GeoTIFF to B2 storage (`satellite/chlorophyll/nasa/YYYY-MM-DD.tif`).
- **Acceptance Criteria**:
  - [ ] Fetches daily MODIS satellite rasters via Google Earth Engine API.
  - [ ] Exports clipped GeoTIFF files to Backblaze B2.

##### [CHUNK_ID: R4-C04] NOAA Tides & Weather Data Ingestor
- **Role**: Role 4 (Data Pipeline Engineer)
- **Target Files**: `pipeline/ingestion/noaa_ingestor.py`
- **Prerequisites**: `[R4-C01]`
- **Inputs**: NOAA CO-OPS REST API, NOAA GFS Wave API
- **Outputs**: Tide predictions and GFS wave forecast JSON in Backblaze B2
- **Implementation Steps**:
  1. Query NOAA CO-OPS API for predicted astronomical water levels along major Indian coastal ports.
  2. Query NOAA GFS Wave model endpoints for wave height, direction, and swell period predictions.
  3. Save normalized JSON objects to B2 (`weather/noaa/YYYY-MM-DD.json`).
- **Acceptance Criteria**:
  - [ ] Ingests tide tables and wave forecasts cleanly.
  - [ ] Uploads structured JSON to Backblaze B2.

##### [CHUNK_ID: R4-C05] INCOIS Advisory Web Scraper
- **Role**: Role 4 (Data Pipeline Engineer)
- **Target Files**: `pipeline/ingestion/incois_scraper.py`
- **Prerequisites**: `[R4-C01]`
- **Inputs**: INCOIS portal bulletin web pages / PDFs
- **Outputs**: Structured INCOIS PFZ and OSF sector advisory JSON in B2
- **Implementation Steps**:
  1. Write BeautifulSoup / PyPDF scraper fetching daily PFZ bulletins and Ocean State Forecast (OSF) sector pages from INCOIS portal.
  2. Parse sector numbers, latitude/longitude coordinates, SST values, and validity timestamps.
  3. Save JSON payload to B2 (`advisories/pfz/YYYY-MM-DD.json`) and forward text to vector indexer.
- **Acceptance Criteria**:
  - [ ] Parses INCOIS daily bulletins into structured JSON data.
  - [ ] Uploads advisory JSON to B2 and vector store pipeline.

##### [CHUNK_ID: R4-C06] IMD Marine Warning Scraper
- **Role**: Role 4 (Data Pipeline Engineer)
- **Target Files**: `pipeline/ingestion/imd_scraper.py`
- **Prerequisites**: `[R4-C01]`
- **Inputs**: IMD Mausam coastal warning feeds
- **Outputs**: Structured IMD fishermen warnings and cyclone alert JSON in B2
- **Implementation Steps**:
  1. Scrape IMD Mausam marine weather bulletin RSS feeds and coastal warning HTML pages.
  2. Extract hazard type (squally weather, port signals, cyclone depression), coastal sector tags, and validity period.
  3. Save normalized JSON payload to B2 (`weather/imd/YYYY-MM-DD.json`).
- **Acceptance Criteria**:
  - [ ] Extracts active IMD fishermen warnings cleanly.
  - [ ] Uploads hazard warning JSON to Backblaze B2.

##### [CHUNK_ID: R4-C07] Scientific NetCDF & GeoTIFF Raster Processor
- **Role**: Role 4 (Data Pipeline Engineer)
- **Target Files**: `pipeline/processors/netcdf_processor.py`, `geotiff_processor.py`
- **Prerequisites**: `[R4-C02]`, `[R4-C03]`
- **Inputs**: Raw NetCDF and GeoTIFF files from B2
- **Outputs**: Processed vector GeoJSON tiles for map rendering
- **Implementation Steps**:
  1. Use `xarray`, `netCDF4`, and `rasterio` Python libraries to open raw satellite raster files.
  2. Extract data arrays for SST and Chlorophyll-a. Interpolate missing data points caused by cloud cover.
  3. Convert grid rasters into lightweight vector GeoJSON tile files for fast map layer display on client.
- **Acceptance Criteria**:
  - [ ] Converts heavy scientific raster files into lightweight GeoJSON tiles.
  - [ ] Handles missing data interpolation cleanly.

##### [CHUNK_ID: R4-C08] Dataset Freshness Tracker & Health Logger
- **Role**: Role 4 (Data Pipeline Engineer)
- **Target Files**: `pipeline/storage/db_writer.py`
- **Prerequisites**: `[R4-C01]`
- **Inputs**: Ingestion job status metadata
- **Outputs**: PostgreSQL database records tracking dataset freshness
- **Implementation Steps**:
  1. Maintain database table `data_freshness` (`dataset_name`, `last_updated`, `status`, `record_count`, `file_size_bytes`).
  2. Update table record automatically at the end of each ingestor pipeline run.
  3. Expose dataset freshness metadata to backend REST API.
- **Acceptance Criteria**:
  - [ ] `data_freshness` table updates reliably after pipeline runs.
  - [ ] Failed ingestion attempts log status `FAILED` with error stack trace.

##### [CHUNK_ID: R4-C09] Automated ETL Scheduler Engine
- **Role**: Role 4 (Data Pipeline Engineer)
- **Target Files**: `pipeline/schedulers/cron_config.py`, `pipeline_runner.py`
- **Prerequisites**: `[R4-C02]`, `[R4-C03]`, `[R4-C04]`, `[R4-C05]`, `[R4-C06]`
- **Inputs**: Cron schedule configuration
- **Outputs**: Automated execution of all pipeline ingestors on background schedule
- **Implementation Steps**:
  1. Configure `APScheduler` in Python to execute ingestion jobs on cron schedules: Copernicus (every 6h), NASA GEE (daily at 02:00 UTC), NOAA (every 3h), INCOIS/IMD scrapers (every 6h).
  2. Add automatic error retry logic (3 attempts with exponential backoff).
- **Acceptance Criteria**:
  - [ ] Pipeline runner executes scheduled jobs automatically in background.
  - [ ] Retries failed jobs gracefully.

##### [CHUNK_ID: R4-C10] RAG Advisory Vector Store Indexer
- **Role**: Role 4 (Data Pipeline Engineer)
- **Target Files**: `pipeline/storage/vector_indexer.py`
- **Prerequisites**: `[R4-C05]`, `[R4-C06]`
- **Inputs**: Scraped text advisories and marine guideline documents
- **Outputs**: ChromaDB vector store collection updated with advisory embeddings
- **Implementation Steps**:
  1. Read scraped INCOIS advisories, IMD warning bulletins, and marine guidelines.
  2. Split text into semantic chunks using `RecursiveCharacterTextSplitter` (chunk_size=500, overlap=50).
  3. Generate embeddings using `sentence-transformers/all-MiniLM-L6-v2` and upsert into local ChromaDB vector database with source metadata tags.
- **Acceptance Criteria**:
  - [ ] Text advisories are chunked, embedded, and indexed into ChromaDB.
  - [ ] Metadata tags (source, date, sector) are preserved for citation retrieval.

---

#### 9.7.5 ROLE 5: Geospatial & Map Services Engineer (`geo/`)

##### [CHUNK_ID: R5-C01] Geodatabase Seeding & Boundary Manager
- **Role**: Role 5 (Geospatial Engineer)
- **Target Files**: `geo/services/boundary_service.py`, `geo/boundaries/`
- **Prerequisites**: None
- **Inputs**: Boundary GeoJSON/Shapefiles (EEZ, MPAs, Fishing Sectors)
- **Outputs**: PostGIS database tables populated with spatial boundary geometries
- **Implementation Steps**:
  1. Download/clean GeoJSON shapefiles for India EEZ, Marine Protected Areas (MPAs), International Maritime Boundary Line (IMBL), and INCOIS 14 fishing sectors.
  2. Write Python script using `GeoPandas` and `GeoAlchemy2` to load geometries into PostGIS spatial tables.
- **Acceptance Criteria**:
  - [ ] Spatial tables populated with valid 2D polygon geometries in EPSG:4326.
  - [ ] PostGIS spatial indexes (`GIST`) created for fast spatial lookup.

##### [CHUNK_ID: R5-C02] Spatial Point-in-Polygon Query Engine
- **Role**: Role 5 (Geospatial Engineer)
- **Target Files**: `geo/services/boundary_service.py`
- **Prerequisites**: `[R5-C01]`
- **Inputs**: Point coordinates `(lat, lon)`
- **Outputs**: `BoundaryCheck` Pydantic payload indicating zone containment and warnings
- **Implementation Steps**:
  1. Write PostGIS SQL query using `ST_Contains(geometry, ST_MakePoint(lon, lat))` and `ST_DWithin`.
  2. Return boolean flags: `is_inside_eez`, `is_inside_mpa`, `is_restricted`, `is_fishing_ban_active`.
  3. Return zone metadata and legal warning text if point is inside a restricted polygon.
- **Acceptance Criteria**:
  - [ ] Accurately determines zone containment for coordinates in Indian waters.
  - [ ] Returns zone name and warning text cleanly.

##### [CHUNK_ID: R5-C03] Real-Time Proximity & Geofencing Monitor
- **Role**: Role 5 (Geospatial Engineer)
- **Target Files**: `geo/services/geofence_service.py`
- **Prerequisites**: `[R5-C01]`
- **Inputs**: Vessel location `(lat, lon)`, heading, speed
- **Outputs**: Geofence proximity alert payload with distance and bearing to nearest border
- **Implementation Steps**:
  1. Implement shortest-distance algorithm from point `(lat, lon)` to nearest restricted boundary line using PostGIS `ST_Distance`.
  2. Compute warning severity: `< 10 km` = Caution Alert; `< 2 km` = Critical Hazard Alert.
  3. Return alert payload with distance (km), direction, and warning message.
- **Acceptance Criteria**:
  - [ ] Calculates shortest distance to boundaries accurately.
  - [ ] Emits proximity warning alerts when vessel enters safety buffer.

##### [CHUNK_ID: R5-C04] Spatial PFZ Nearest Neighbor Calculator
- **Role**: Role 5 (Geospatial Engineer)
- **Target Files**: `geo/analysis/pfz_analyzer.py`
- **Prerequisites**: `[R5-C01]`
- **Inputs**: User coordinates `(lat, lon)`, active PFZ geometries
- **Outputs**: Ranked array of top 3 nearest Potential Fishing Zones with distance and ETA
- **Implementation Steps**:
  1. Query active PFZ geometries for today's date.
  2. Calculate distance in nautical miles using PostGIS `ST_Distance(geography)`.
  3. Calculate compass bearing (e.g. "NE at 45°") and estimated travel time assuming standard cruise speed (8 knots).
  4. Return top 3 nearest PFZs.
- **Acceptance Criteria**:
  - [ ] Returns nearest PFZ locations ordered by proximity.
  - [ ] Computes distance in nautical miles and estimated travel time accurately.

##### [CHUNK_ID: R5-C05] Route Risk Evaluator Component
- **Role**: Role 5 (Geospatial Engineer)
- **Target Files**: `geo/services/route_service.py`
- **Prerequisites**: `[R5-C02]`
- **Inputs**: Polyline waypoints array `[[lat1, lon1], [lat2, lon2], ...]`
- **Outputs**: Safety-annotated route GeoJSON polyline with segment risk scores
- **Implementation Steps**:
  1. Interpolate sample points every 1 km along input route polyline.
  2. Query underlying wave height, wind speed, current speed, and boundary intersections at each sample point.
  3. Assign segment risk score: Green (safe), Yellow (caution), Red (danger).
  4. Return GeoJSON FeatureCollection polyline styled by risk segment.
- **Acceptance Criteria**:
  - [ ] Route is evaluated for environmental hazards along its entire path.
  - [ ] Returns color-coded GeoJSON polyline.

##### [CHUNK_ID: R5-C06] SST & Chlorophyll Map Layer Service
- **Role**: Role 5 (Geospatial Engineer)
- **Target Files**: `geo/layers/layer_manager.py`, `sst_layer.py`, `chlorophyll_layer.py`
- **Prerequisites**: `[R5-C01]`
- **Inputs**: Bounding box query parameters
- **Outputs**: Formatted GeoJSON layer payloads for map display
- **Implementation Steps**:
  1. Read processed GeoJSON rasters from Backblaze B2 storage cache.
  2. Filter features matching requested bounding box coordinates.
  3. Simplify polygon vertices based on target map zoom level to optimize payload size.
  4. Return formatted GeoJSON payload.
- **Acceptance Criteria**:
  - [ ] Serves GeoJSON layer payloads filtered by bounding box.
  - [ ] Vertex simplification reduces load time on client maps.

##### [CHUNK_ID: R5-C07] Composite Environmental Risk Heatmap Generator
- **Role**: Role 5 (Geospatial Engineer)
- **Target Files**: `geo/analysis/risk_calculator.py`, `risk_layer.py`
- **Prerequisites**: `[R5-C06]`
- **Inputs**: Wind, Wave, Current, and IMD Warning grid datasets
- **Outputs**: Composite spatial risk heatmap GeoJSON grid
- **Implementation Steps**:
  1. Divide Indian coastal waters into a 0.1° x 0.1° spatial grid.
  2. Calculate cell risk score: `Risk = (Wind_Score * 0.3) + (Wave_Score * 0.4) + (Warning_Score * 0.3)`.
  3. Export grid as GeoJSON FeatureCollection colored from green (0.0) to red (1.0).
- **Acceptance Criteria**:
  - [ ] Generates composite risk grid correctly combining wind, wave, and warning factors.
  - [ ] Exports valid GeoJSON heatmap grid.

##### [CHUNK_ID: R5-C08] Spatial Area Query Aggregator
- **Role**: Role 5 (Geospatial Engineer)
- **Target Files**: `geo/services/spatial_query_service.py`
- **Prerequisites**: `[R5-C06]`
- **Inputs**: Drawn polygon coordinates from frontend map UI
- **Outputs**: Summary statistics dictionary for target area
- **Implementation Steps**:
  1. Accept polygon coordinates drawn by user on map UI.
  2. Perform spatial intersection (`ST_Intersects`) against underlying SST, Chlorophyll, Wind, and Wave grid points.
  3. Calculate aggregate summary stats: `min_sst`, `max_sst`, `avg_chlorophyll`, `max_wave_height`, `active_warnings_count`.
- **Acceptance Criteria**:
  - [ ] Computes min/max/avg environmental metrics inside user polygon.
  - [ ] Returns summary statistics JSON payload.

##### [CHUNK_ID: R5-C09] Temporal Environmental Trend Analyzer
- **Role**: Role 5 (Geospatial Engineer)
- **Target Files**: `geo/analysis/trend_analyzer.py`
- **Prerequisites**: `[R5-C06]`
- **Inputs**: Target coordinates `(lat, lon)`, time range (7d / 30d)
- **Outputs**: Time-series trend array and anomaly detection flags
- **Implementation Steps**:
  1. Query historical raster values for target coordinate from B2 storage archive over 7-day and 30-day windows.
  2. Compute rolling average, standard deviation, and trend slope.
  3. Detect anomaly events (e.g. Marine Heatwave defined as SST > 2°C above 30-day mean).
- **Acceptance Criteria**:
  - [ ] Returns historical time-series array for coordinates.
  - [ ] Flags environmental anomalies correctly.

##### [CHUNK_ID: R5-C10] GeoJSON Simplification & Tile Optimizer
- **Role**: Role 5 (Geospatial Engineer)
- **Target Files**: `geo/layers/layer_manager.py`
- **Prerequisites**: `[R5-C06]`
- **Inputs**: Raw GeoJSON layers
- **Outputs**: Optimized, lightweight GeoJSON payloads for mobile web rendering
- **Implementation Steps**:
  1. Apply Douglas-Peucker polygon simplification algorithm (`ST_SimplifyPreserveTopology`) on heavy boundary geometries.
  2. Truncate coordinate decimal precision to 5 decimal places (~1m accuracy).
  3. Reduce spatial payload size by up to 60% for rapid network transmission.
- **Acceptance Criteria**:
  - [ ] GeoJSON file sizes reduced significantly without visible geometry distortion.
  - [ ] Map layer load latency drops below 200ms.

---

#### 9.7.6 ROLE 6: NLP, Multilingual & RAG Engineer (`nlp/`)

##### [CHUNK_ID: R6-C01] Fast Language Identification Engine
- **Role**: Role 6 (NLP & Multilingual Engineer)
- **Target Files**: `nlp/detection/language_detector.py`
- **Prerequisites**: None
- **Inputs**: User input text string
- **Outputs**: ISO language code (`en`, `hi`, `ta`, `ml`, `te`, `kn`, `or`, `bn`, `mr`, `gu`)
- **Implementation Steps**:
  1. Configure `fastText` or `langdetect` language identification library for Indian languages.
  2. Implement `detect_language(text)` returning primary language code and confidence rating.
  3. Default to English (`en`) if confidence is below threshold.
- **Acceptance Criteria**:
  - [ ] Accurately identifies 10 Indian coastal languages from sample query strings.
  - [ ] Handles short and conversational queries cleanly.

##### [CHUNK_ID: R6-C02] IndicTrans2 Machine Translation Service
- **Role**: Role 6 (NLP & Multilingual Engineer)
- **Target Files**: `nlp/translation/translator.py`
- **Prerequisites**: `[R6-C01]`
- **Inputs**: Input text string, source language code, target language code
- **Outputs**: Translated text string
- **Implementation Steps**:
  1. Create translation pipeline wrapping AI4Bharat `IndicTrans2` model (or fallback API).
  2. Implement `translate_to_english(text, src_lang)` to translate incoming query for agent processing.
  3. Implement `translate_from_english(text, tgt_lang)` to translate final agent answer to user's language.
- **Acceptance Criteria**:
  - [ ] Translates regional queries to English and agent answers back to regional language.
  - [ ] Preserves formatting tags and numerical values.

##### [CHUNK_ID: R6-C03] Marine & Fisheries Domain Glossary
- **Role**: Role 6 (NLP & Multilingual Engineer)
- **Target Files**: `nlp/translation/marine_glossary.py`
- **Prerequisites**: `[R6-C02]`
- **Inputs**: English text containing technical marine terms
- **Outputs**: Translated text preserving accurate technical marine terminology
- **Implementation Steps**:
  1. Build JSON dictionary of 200+ marine terms ("Potential Fishing Zone", "Sea Surface Temperature", "Tidal Bore", "Squally Weather", "Swell Wave") across 10 languages.
  2. Tag technical terms in text before translation.
  3. Replace translated terms with canonical domain glossary translations post-translation.
- **Acceptance Criteria**:
  - [ ] Technical marine terms translate accurately across all supported languages.
  - [ ] Prevents literal/incorrect translations of specialized terminology.

##### [CHUNK_ID: R6-C04] Operational Intent Classification Engine
- **Role**: Role 6 (NLP & Multilingual Engineer)
- **Target Files**: `nlp/detection/intent_classifier.py`
- **Prerequisites**: `[R6-C01]`
- **Inputs**: User query string
- **Outputs**: Intent classification category and confidence score
- **Implementation Steps**:
  1. Implement intent classifier assigning queries to categories: `PFZ_LOCATION`, `SAFETY_CHECK`, `WEATHER_FORECAST`, `ROUTE_RISK`, `GEOFENCE_CHECK`, `GENERAL_KNOWLEDGE`.
  2. Train/configure zero-shot classifier or fine-tuned model.
  3. Output primary intent category to Planner Agent for task decomposition.
- **Acceptance Criteria**:
  - [ ] Achieves > 90% accuracy on marine query test set.
  - [ ] Passes classified intent tag to Planner Agent.

##### [CHUNK_ID: R6-C05] Speech-To-Text Audio Transcription Pipeline
- **Role**: Role 6 (NLP & Multilingual Engineer)
- **Target Files**: `nlp/voice/stt_engine.py`
- **Prerequisites**: `[R6-C01]`
- **Inputs**: Base64 audio payload or audio file path (`audio/wav`, `audio/webm`)
- **Outputs**: Transcribed query text string and detected language code
- **Implementation Steps**:
  1. Implement STT service wrapping OpenAI `Whisper` model (`small` or `medium` size).
  2. Accept audio blob from frontend, run Whisper transcription, and extract spoken text.
  3. Run language detector on transcribed text to identify spoken language.
- **Acceptance Criteria**:
  - [ ] Transcribes audio recordings cleanly into text.
  - [ ] Identifies spoken language code accurately.

##### [CHUNK_ID: R6-C06] Regional Text-To-Speech Audio Generator
- **Role**: Role 6 (NLP & Multilingual Engineer)
- **Target Files**: `nlp/voice/tts_engine.py`
- **Prerequisites**: `[R6-C02]`
- **Inputs**: Response text string, target language code
- **Outputs**: MP3 audio file URL for client playback
- **Implementation Steps**:
  1. Implement TTS service using `gTTS` (Google Text-to-Speech) or `Coqui TTS`.
  2. Convert response text into audio stream in user's target language.
  3. Save MP3 file to server static directory and return audio file URL (`/static/audio/{id}.mp3`).
- **Acceptance Criteria**:
  - [ ] Generates clear spoken audio MP3 in regional languages.
  - [ ] Returns valid playable audio URL.

##### [CHUNK_ID: R6-C07] RAG Document Chunking & Ingestion Engine
- **Role**: Role 6 (NLP & Multilingual Engineer)
- **Target Files**: `nlp/rag/document_loader.py`
- **Prerequisites**: None
- **Inputs**: Advisory PDFs, IMD manuals, government policy documents
- **Outputs**: Formatted text chunks with metadata tags
- **Implementation Steps**:
  1. Load INCOIS advisories, IMD weather manuals, and PM-MSY policy documents.
  2. Split text into semantic chunks using `RecursiveCharacterTextSplitter` (chunk_size=500, chunk_overlap=50).
  3. Attach rich metadata tags (document_title, source, section, validity_date).
- **Acceptance Criteria**:
  - [ ] Documents chunked cleanly without truncating technical guidelines.
  - [ ] Metadata tags attached to all chunks.

##### [CHUNK_ID: R6-C08] Vector Semantic Search & Context Retriever
- **Role**: Role 6 (NLP & Multilingual Engineer)
- **Target Files**: `nlp/rag/retriever.py`
- **Prerequisites**: `[R6-C07]`
- **Inputs**: Query embedding string, top_k parameter
- **Outputs**: Relevant advisory text chunks with similarity scores and citations
- **Implementation Steps**:
  1. Initialize ChromaDB vector store client with `sentence-transformers/all-MiniLM-L6-v2` embedding model.
  2. Perform vector similarity search for input query, retrieving top-k (k=3) matching chunks.
  3. Format retrieved context with source document citation tags for Explainer Agent.
- **Acceptance Criteria**:
  - [ ] Retrieves relevant advisory chunks matching user query.
  - [ ] Preserves document citations for explainability output.

##### [CHUNK_ID: R6-C09] Multi-Lingual Response Templating Engine
- **Role**: Role 6 (NLP & Multilingual Engineer)
- **Target Files**: `nlp/templates/response_templates.py`, `alert_templates.py`
- **Prerequisites**: `[R6-C02]`
- **Inputs**: Structured agent decision data
- **Outputs**: Standardized markdown response template text across languages
- **Implementation Steps**:
  1. Create template strings for Safety Warnings, PFZ Bulletins, Weather Reports, and Route Advisories.
  2. Ensure safety indicators (🔴 DANGER, 🟡 CAUTION, 🟢 SAFE) and tables remain intact across all language translations.
- **Acceptance Criteria**:
  - [ ] Response templates output consistent layout across all 10 languages.
  - [ ] Safety alert indicators remain prominent.

##### [CHUNK_ID: R6-C10] Explainability & Data Provenance Formatter
- **Role**: Role 6 (NLP & Multilingual Engineer)
- **Target Files**: `nlp/templates/response_templates.py`
- **Prerequisites**: `[R6-C08]`, `[R6-C09]`
- **Inputs**: Agent execution state, dataset metadata
- **Outputs**: Evidence citation block translated into user's language
- **Implementation Steps**:
  1. Construct evidence trail section: "Data Sources: [INCOIS, Copernicus, IMD]. Timestamps: [...]. Threshold Factors: [...]. Confidence Rating: High."
  2. Translate evidence block into user's language while preserving technical source names and timestamps.
- **Acceptance Criteria**:
  - [ ] Evidence trail section details data sources, timestamps, and reasoning.
  - [ ] Translates cleanly to user's native language.

---

## 10. Shared Contracts — The Glue Between Roles

> [!CAUTION]
> **All 6 roles must agree on these schemas before starting individual work.** Define them on Day 1 of the hackathon. They live in `shared/schemas/` and are imported by every module.

### 10.1 Chat Schema (`shared/schemas/chat_schema.py`)

```python
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"

class MapAction(BaseModel):
    """Instruction for frontend to update the map"""
    action: str                 # "add_layer", "highlight_zone", "draw_route", "show_popup"
    layer_type: Optional[str]   # "sst", "chlorophyll", "risk", "pfz", "boundary"
    geojson: Optional[dict]     # GeoJSON data to render
    center: Optional[List[float]]  # [lat, lon] to pan to
    zoom: Optional[int]

class ChatMessage(BaseModel):
    session_id: str
    role: MessageRole
    content: str
    language: str = "en"
    timestamp: str
    map_actions: Optional[List[MapAction]] = None
    charts: Optional[List[dict]] = None
    evidence: Optional[dict] = None
    audio_url: Optional[str] = None

class ChatRequest(BaseModel):
    session_id: str
    message: str               # Text or transcribed voice
    language: Optional[str]    # Auto-detected if not provided
    location: Optional[List[float]]  # [lat, lon] from device GPS
    audio_base64: Optional[str]  # Raw audio for STT
```

### 10.2 Marine Data Schema (`shared/schemas/marine_schema.py`)

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MarineConditions(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime
    sst: Optional[float]              # °C
    chlorophyll: Optional[float]       # mg/m³
    wind_speed: Optional[float]        # km/h
    wind_direction: Optional[float]    # degrees
    wave_height: Optional[float]       # meters
    wave_period: Optional[float]       # seconds
    current_speed: Optional[float]     # m/s
    current_direction: Optional[float] # degrees
    tide_level: Optional[float]        # meters
    source: str                        # "copernicus", "noaa", "incois", etc.
    freshness: str                     # ISO timestamp of source data

class SafetyAssessment(BaseModel):
    risk_level: str                    # "safe", "caution", "danger"
    risk_score: float                  # 0.0 to 1.0
    factors: list[str]                 # ["high_wind", "rough_seas", "cyclone_alert"]
    recommendation: str
    evidence: dict                     # Source data used for assessment
```

### 10.3 Geo Schema (`shared/schemas/geo_schema.py`)

```python
from pydantic import BaseModel
from typing import Optional, List

class BoundaryCheck(BaseModel):
    is_inside_eez: bool
    is_inside_mpa: bool
    is_restricted: bool
    is_fishing_ban_active: bool
    nearest_boundary: Optional[str]
    distance_to_boundary_km: Optional[float]
    zone_name: Optional[str]
    warning_message: Optional[str]

class PFZResult(BaseModel):
    zone_id: str
    center: List[float]            # [lat, lon]
    distance_km: float
    bearing: str                   # "NE", "SW", etc.
    sst: float
    chlorophyll: float
    advisory_date: str
    source: str                    # "incois_pfz"
```

---

## 11. API Contract Summary

> [!NOTE]
> Frontend (Role 1) calls these. Backend (Role 2) implements the HTTP layer. Agents/Geo/NLP/Pipeline provide the business logic behind them.

| Endpoint | Method | Owner | Consumer | Description |
|----------|--------|-------|----------|-------------|
| `/ws/chat` | WebSocket | Role 2 | Role 1 | Real-time chat (send message → stream response) |
| `/api/map/layers/{type}` | GET | Role 2 + 5 | Role 1 | GeoJSON layers (sst, chlorophyll, risk, pfz, boundaries) |
| `/api/data/current` | GET | Role 2 + 4 | Role 1, 3 | Current conditions at lat/lon |
| `/api/data/freshness` | GET | Role 2 + 4 | Role 3 | Last-updated timestamps per data source |
| `/api/alerts` | GET | Role 2 + 5 | Role 1 | Active alerts for lat/lon |
| `/api/alerts/subscribe` | POST | Role 2 | Role 1 | Subscribe to push alerts |
| `/api/feedback` | POST | Role 2 | Role 1 | Submit recommendation feedback |
| `/api/tts` | POST | Role 2 + 6 | Role 1 | Text-to-speech (returns audio URL) |
| `/api/health` | GET | Role 2 | DevOps | Server health check |

---

## 12. Development Workflow & Conventions

### 12.1 Git Branching

```
main                    ← protected, deploy from here
├── dev                 ← integration branch, all PRs merge here
│   ├── feat/frontend-chat        ← Role 1 branches
│   ├── feat/frontend-map
│   ├── feat/backend-api          ← Role 2 branches
│   ├── feat/backend-websocket
│   ├── feat/agents-planner       ← Role 3 branches
│   ├── feat/agents-weather
│   ├── feat/pipeline-copernicus  ← Role 4 branches
│   ├── feat/pipeline-scheduler
│   ├── feat/geo-boundaries       ← Role 5 branches
│   ├── feat/geo-routes
│   ├── feat/nlp-translation      ← Role 6 branches
│   └── feat/nlp-rag
```

### 12.2 Integration Points

```
Day 1 (hours 0–6):
  → All roles: Agree on shared schemas, set up repos, bootstrap individual modules
  → Role 2: Deploy minimal FastAPI with health + WebSocket echo
  → Role 1: Deploy minimal React app connecting to backend

Day 1 (hours 6–12):
  → Roles 3–6: Build individual modules with mock data
  → Role 4: First data pipeline run → data in B2
  → Role 2: Wire mock agent response to WebSocket

Day 2 (hours 12–24):
  → Integration: Connect real agents to WebSocket via backend
  → Role 1 + 5: Map layers served from real B2 data
  → Role 6: Translation + voice pipeline connected

Day 2 (hours 24–36):
  → End-to-end testing: Full chat → agent → response → map flow
  → Polish: UI animations, error handling, edge cases
  → Demo prep: Pre-seed B2 with demo data for reliable demo
```

---

## 13. Demo Strategy — Pre-Seeded Data

> [!TIP]
> For a reliable hackathon demo, pre-seed Backblaze B2 with a known-good dataset for the Indian Ocean / a specific coastal region (e.g., Kerala coast). This ensures the demo works even if live APIs are slow or down.

### Pre-seed checklist:
- [ ] 3 days of SST data (Copernicus) for Kerala/Tamil Nadu coast
- [ ] 3 days of chlorophyll data (NASA MODIS) for same region
- [ ] NOAA tide data for Kochi/Chennai
- [ ] 1 INCOIS PFZ advisory (parsed to JSON)
- [ ] 1 IMD marine weather bulletin (parsed to JSON)
- [ ] EEZ India boundary GeoJSON
- [ ] 3 MPA polygons for demo region
- [ ] 1 fishing ban zone polygon

---

## 14. Success Criteria (for SIH Judges)

| Criterion | How ORCA Demonstrates It |
|-----------|--------------------------|
| **Agentic AI** | Multi-agent LangGraph with autonomous planning, tool selection, task execution |
| **Conversational interface** | Multi-turn NL chat with context memory, not menu-driven |
| **Multi-source correlation** | Single response synthesizes SST + weather + tides + alerts + boundaries |
| **Explainability** | Every response cites sources, shows reasoning, displays evidence |
| **Multilingual** | Auto-detect language, respond in same language, voice I/O |
| **Geospatial** | Interactive map linked to chat, geofencing, route optimization |
| **Near-real-time** | Global API data supplements INCOIS batch advisories |
| **Safety** | Proactive alerts, risk scoring, boundary warnings |
| **Innovation** | No existing product combines all above capabilities |
| **Feasibility** | 100% free/OSS stack, working prototype |

---

## 15. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| INCOIS/IMD have no public API | Pre-scrape + cache data in B2; use global sources as fallback |
| Gemini API rate limits (15 RPM free) | Cache agent responses for similar queries; batch planning |
| Large NLP models don't fit on student laptops | Use Whisper `small`, IndicTrans2 `base`; offload to free cloud GPU (Colab) if needed |
| Satellite data latency / cloud cover gaps | Use forecast models (NOAA) + historical trends to fill gaps; disclose in evidence |
| Team member blocked by dependency on another | Shared schemas agreed Day 1; each role has mock data to develop against |
| Demo connectivity issues | Pre-seed B2 with demo dataset; local Docker fallback |

import sys
import os
from pathlib import Path

# Ensure root workspace directory is on sys.path so modules like geo, nlp, agents, shared resolve
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from server.src.middleware.cors import setup_cors_middleware
from server.src.routes.health import router as health_router
from server.src.routes.chat import router as chat_router
from server.src.routes.map_data import router as map_router, spatial_router, ais_router

app = FastAPI(
    title="NeerMitra Modular API (orca/ architecture)",
    description="Role 2 Backend Engineer API Gateway routing between AI Agents, Geospatial, and NLP",
    version="2.0.0"
)

# Setup CORS
setup_cors_middleware(app)

# Include Routers
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(map_router)
app.include_router(spatial_router)
app.include_router(ais_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.src.app:app", host="0.0.0.0", port=8000, reload=True)

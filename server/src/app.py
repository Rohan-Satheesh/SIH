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
from server.src.routes.nlp_health import router as nlp_health_router
from server.src.routes.alerts import router as alerts_router
from server.src.routes.data import router as data_router
from server.src.routes.feedback import router as feedback_router

app = FastAPI(
    title="ORCA Marine Intelligence Platform API",
    description="Agentic AI backend for ocean weather, PFZ advisory, geospatial intelligence, and safety monitoring.",
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
app.include_router(nlp_health_router)
app.include_router(alerts_router)
app.include_router(data_router)
app.include_router(feedback_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.src.app:app", host="0.0.0.0", port=8000, reload=True)


import logging

from fastapi import APIRouter
from datetime import datetime, timezone
from sqlalchemy import text
from server.src.config.database import get_db_engine
from geo.layers.layer_manager import get_all_available_layers
from server.src.config.settings import MARINETRAFFIC_API_KEY

router = APIRouter(tags=["Health & Status"])
logger = logging.getLogger(__name__)


def _has_postgis_connection(engine) -> bool:
    if engine is None:
        return False

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_extension
                        WHERE extname = 'postgis'
                    );
                    """
                )
            )
            return bool(result.scalar())
    except Exception:
        logger.exception("PostGIS health check failed")
        return False

@router.get("/")
def read_root():
    engine = get_db_engine()
    layers = get_all_available_layers(engine)
    return {
        "status": "NeerMitra Marine Intelligence Core Online",
        "postgis_connected": engine is not None,
        "active_spatial_layers": list(layers.keys()),
        "architecture": "6-Role Monorepo Model (orca/)",
        "engine_version": "2.0.0 (PostGIS + GeoPandas Dual Core)"
    }

@router.get("/api/status")
def api_status():
    engine = get_db_engine()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "postgis_connected": _has_postgis_connection(engine),
        "available_layers": list(get_all_available_layers(engine).keys()),
        "ais_configured": bool(MARINETRAFFIC_API_KEY),
    }

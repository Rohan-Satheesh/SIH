"""
ORCA / NeerMitra — Multi-Turn Session State Manager
PRD Reference: CHUNK_ID R2-C09

Gives the `sessions` table (see `server/src/models/session.py`) a durable
place to record per-conversation context: last known language, vessel type,
location, and last query text. This is intentionally a thin, best-effort
persistence helper — it does not (yet) feed back into the LangGraph
orchestrator's own conversation memory (`agents/memory/`); it exists so that
data isn't lost, and so a future feature (e.g. resuming a session after a
page reload, or a background alert broadcaster keyed by last known location)
has somewhere real to read from.

Every function here is safe to call from a hot request path: failures are
caught and logged, never raised, so a missing/unreachable database can never
break `/api/chat` or any other endpoint.
"""

import logging
from typing import Optional, List

from server.src.config.database import get_db_session
from server.src.models.session import Session as SessionModel

logger = logging.getLogger("orca.session_manager")


def upsert_session(
    session_id: str,
    language: Optional[str] = None,
    vessel_type: Optional[str] = None,
    location: Optional[List[float]] = None,
    last_query: Optional[str] = None,
) -> bool:
    """
    Create or update the durable session record for `session_id`.
    Returns True if the write reached the database, False otherwise
    (no database configured, database unreachable, or any other error).
    """
    if not session_id:
        return False

    try:
        with get_db_session() as db:
            if db is None:
                return False

            record = db.get(SessionModel, session_id)
            if record is None:
                record = SessionModel(session_id=session_id)
                db.add(record)

            if language is not None:
                record.language = language
            if vessel_type is not None:
                record.vessel_type = vessel_type
            if location and len(location) == 2:
                record.latitude, record.longitude = location[0], location[1]
            if last_query is not None:
                record.last_query = last_query

            return True
    except Exception:
        logger.exception("upsert_session failed for session_id=%r; continuing without it.", session_id)
        return False


def get_session(session_id: str) -> Optional[dict]:
    """
    Retrieve the durable session record for `session_id`, or None if it
    doesn't exist / the database is unavailable.
    """
    if not session_id:
        return None

    try:
        with get_db_session() as db:
            if db is None:
                return None

            record = db.get(SessionModel, session_id)
            if record is None:
                return None

            return {
                "session_id": record.session_id,
                "language": record.language,
                "vessel_type": record.vessel_type,
                "location": (
                    [record.latitude, record.longitude]
                    if record.latitude is not None and record.longitude is not None
                    else None
                ),
                "last_query": record.last_query,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None,
            }
    except Exception:
        logger.exception("get_session failed for session_id=%r.", session_id)
        return None

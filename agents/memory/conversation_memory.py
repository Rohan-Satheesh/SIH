import uuid
from typing import Dict, Any, Optional, Tuple

SESSION_STORE: Dict[str, Dict[str, Any]] = {}

def get_or_create_session(session_id: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    """Retrieves or initializes a multi-turn conversation session."""
    sid = session_id if session_id and session_id.strip() else str(uuid.uuid4())[:8]
    if sid not in SESSION_STORE:
        SESSION_STORE[sid] = {
            "session_id": sid,
            "turns": [],
            "last_location": None,
            "last_pfz": None,
            "last_intent": None
        }
    return sid, SESSION_STORE[sid]

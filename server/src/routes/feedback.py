"""
ORCA Backend — User Feedback Collection Endpoint
PRD Reference: Section 3.8, Section 11 — /api/feedback, CHUNK_ID R2-C07
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import logging

from sqlalchemy import func as sa_func

from server.src.config.database import get_db_session
from server.src.models.feedback import Feedback as FeedbackModel

logger = logging.getLogger("orca.feedback")

router = APIRouter(prefix="/api", tags=["Feedback & Learning"])

# In-memory fallback store, used whenever the database is not configured or
# not reachable, so the endpoint keeps working either way.
feedback_store: list = []


class FeedbackRequest(BaseModel):
    session_id: str = Field("default", description="User session identifier")
    message_id: str = Field(..., description="ID of the message being rated")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5 (1=inaccurate, 5=accurate)")
    is_accurate: bool = Field(True, description="Whether the recommendation was accurate")
    catch_data: Optional[str] = Field(None, description="Optional user-reported catch data")
    comment: Optional[str] = Field(None, description="Optional user comment")


@router.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    """
    Collect user feedback on ORCA advisory quality.
    PRD §3.8: Users can mark recommendations as accurate/inaccurate with optional catch data.
    This drives the reinforcement learning loop.

    Persists to the `feedback` database table when a database is configured
    and reachable; otherwise (and always, as a fast local cache) records the
    submission in an in-memory list so `/feedback/stats` keeps working.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    persisted_to_db = False

    try:
        with get_db_session() as db:
            if db is not None:
                db.add(
                    FeedbackModel(
                        session_id=req.session_id,
                        message_id=req.message_id,
                        rating=req.rating,
                        is_accurate=req.is_accurate,
                        catch_data=req.catch_data,
                        comment=req.comment,
                    )
                )
        # Only reached if the `with` block (including its commit-on-exit) did
        # not raise, so this accurately reflects a completed database write.
        persisted_to_db = db is not None
    except Exception:
        persisted_to_db = False
        logger.exception(
            "Failed to persist feedback to database; continuing with in-memory fallback only."
        )

    entry = {
        "session_id": req.session_id,
        "message_id": req.message_id,
        "rating": req.rating,
        "is_accurate": req.is_accurate,
        "catch_data": req.catch_data,
        "comment": req.comment,
        "submitted_at": now_iso,
    }
    feedback_store.append(entry)

    logger.info(
        "Feedback received: message=%s, rating=%s, accurate=%s, persisted_to_db=%s",
        req.message_id,
        req.rating,
        req.is_accurate,
        persisted_to_db,
    )

    return {
        "status": "received",
        "message": "Thank you for your feedback. This helps improve ORCA's accuracy.",
        "feedback_id": f"fb-{len(feedback_store)}",
        "submitted_at": now_iso,
        "persisted_to_db": persisted_to_db,
    }


@router.get("/feedback/stats")
def feedback_stats():
    """
    Return aggregate feedback statistics.

    Reads from the database when reachable (durable, survives restarts);
    falls back to the in-memory store for this process's lifetime otherwise.
    """
    try:
        with get_db_session() as db:
            if db is not None:
                total = db.query(sa_func.count(FeedbackModel.id)).scalar() or 0
                if total > 0:
                    accurate_count = (
                        db.query(sa_func.count(FeedbackModel.id))
                        .filter(FeedbackModel.is_accurate.is_(True))
                        .scalar()
                        or 0
                    )
                    avg_rating = db.query(sa_func.avg(FeedbackModel.rating)).scalar() or 0
                    return {
                        "total_feedback": total,
                        "accurate_count": accurate_count,
                        "inaccurate_count": total - accurate_count,
                        "accuracy_rate": round(accurate_count / total * 100, 1),
                        "average_rating": round(float(avg_rating), 2),
                        "source": "database",
                    }
    except Exception:
        logger.exception(
            "Failed to read feedback stats from database; falling back to in-memory store."
        )

    total = len(feedback_store)
    accurate_count = sum(1 for f in feedback_store if f.get("is_accurate"))
    avg_rating = sum(f.get("rating", 3) for f in feedback_store) / total if total > 0 else 0

    return {
        "total_feedback": total,
        "accurate_count": accurate_count,
        "inaccurate_count": total - accurate_count,
        "accuracy_rate": round(accurate_count / total * 100, 1) if total > 0 else 0,
        "average_rating": round(avg_rating, 2),
        "source": "in_memory",
    }

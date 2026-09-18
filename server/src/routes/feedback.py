"""
ORCA Backend — User Feedback Collection Endpoint
PRD Reference: Section 3.8, Section 11 — /api/feedback
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import logging
import json

logger = logging.getLogger("orca.feedback")

router = APIRouter(prefix="/api", tags=["Feedback & Learning"])

# In-memory store (in production, this would go to PostgreSQL)
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
    """
    entry = {
        "session_id": req.session_id,
        "message_id": req.message_id,
        "rating": req.rating,
        "is_accurate": req.is_accurate,
        "catch_data": req.catch_data,
        "comment": req.comment,
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }

    feedback_store.append(entry)
    logger.info(f"Feedback received: message={req.message_id}, rating={req.rating}, accurate={req.is_accurate}")

    return {
        "status": "received",
        "message": "Thank you for your feedback. This helps improve ORCA's accuracy.",
        "feedback_id": f"fb-{len(feedback_store)}",
        "submitted_at": entry["submitted_at"]
    }


@router.get("/feedback/stats")
def feedback_stats():
    """Return aggregate feedback statistics."""
    total = len(feedback_store)
    accurate_count = sum(1 for f in feedback_store if f.get("is_accurate"))
    avg_rating = sum(f.get("rating", 3) for f in feedback_store) / total if total > 0 else 0

    return {
        "total_feedback": total,
        "accurate_count": accurate_count,
        "inaccurate_count": total - accurate_count,
        "accuracy_rate": round(accurate_count / total * 100, 1) if total > 0 else 0,
        "average_rating": round(avg_rating, 2),
    }

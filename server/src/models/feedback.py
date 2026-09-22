"""
ORCA / NeerMitra — Feedback Model
PRD Reference: CHUNK_ID R2-C07, Section 3.8 (citizen-science feedback loop)
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func

from server.src.models.base import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, default="default")
    message_id = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    is_accurate = Column(Boolean, nullable=False, default=True)
    catch_data = Column(String, nullable=True)
    comment = Column(String, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

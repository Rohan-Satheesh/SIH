"""
ORCA / NeerMitra — Alert & Alert Subscription Models
PRD Reference: CHUNK_ID R2-C02, R2-C05

`Alert` is a durable record of a hazard advisory (so future work — e.g. a
background broadcaster — has somewhere real to read active alerts from,
instead of the hardcoded seasonal logic in `routes/alerts.py`).

`AlertSubscription` persists push-notification subscriptions submitted via
`POST /api/alerts/subscribe`, which previously were not stored anywhere.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, func

from server.src.models.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hazard_type = Column(String, nullable=False)
    severity = Column(String, nullable=True)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    source = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    issued_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=True)


class AlertSubscription(Base):
    __tablename__ = "alert_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, default="default")
    push_token = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    radius_km = Column(Float, nullable=False, default=50)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

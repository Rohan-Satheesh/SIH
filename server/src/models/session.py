"""
ORCA / NeerMitra — Session Model
PRD Reference: CHUNK_ID R2-C02, R2-C09 (multi-turn session state)

Stores durable per-session context (last known language, vessel type,
location, last query) so a conversation can resume across requests and
across backend restarts. Coordinates are stored as plain lat/lon floats
(not a PostGIS geometry column) so this table works even on a Postgres
instance without the PostGIS extension enabled.
"""

from sqlalchemy import Column, String, Float, DateTime, func

from server.src.models.base import Base


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True)
    language = Column(String, nullable=True)
    vessel_type = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    last_query = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

"""
ORCA / NeerMitra — User Model (optional)
PRD Reference: CHUNK_ID R2-C02 ("User (optional)")

Nothing in the current API requires authentication, so this table is not
referenced by any route yet. It exists so a future login/identity feature
has a durable place to attach to without another migration.
"""

from sqlalchemy import Column, Integer, String, DateTime, func

from server.src.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String, unique=True, nullable=True)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

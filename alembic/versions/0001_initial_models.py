"""Initial models: sessions, feedback, alerts, alert_subscriptions, users

Revision ID: 0001
Revises:
Create Date: 2026-09-22

These tables back PRD CHUNK_ID R2-C02 (Database Schema & PostGIS Migrations)
and R2-C09 (Multi-Turn Session State Manager). Every `create_table` call is
guarded with a `checkfirst`-style inspector check so this migration is safe
to run even if the app's `init_db()` startup safety net
(`server/src/config/database.py`) already created these tables via
`Base.metadata.create_all()` before Alembic was ever run — see
`to_implement.md` for the operational note on reconciling the two.

Revision ID: 0001
Revises: None
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_tables() -> set:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return set(inspector.get_table_names())


def upgrade() -> None:
    existing = _existing_tables()

    if "sessions" not in existing:
        op.create_table(
            "sessions",
            sa.Column("session_id", sa.String(), primary_key=True),
            sa.Column("language", sa.String(), nullable=True),
            sa.Column("vessel_type", sa.String(), nullable=True),
            sa.Column("latitude", sa.Float(), nullable=True),
            sa.Column("longitude", sa.Float(), nullable=True),
            sa.Column("last_query", sa.String(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )

    if "feedback" not in existing:
        op.create_table(
            "feedback",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("session_id", sa.String(), nullable=False, server_default="default"),
            sa.Column("message_id", sa.String(), nullable=False),
            sa.Column("rating", sa.Integer(), nullable=False),
            sa.Column("is_accurate", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("catch_data", sa.String(), nullable=True),
            sa.Column("comment", sa.String(), nullable=True),
            sa.Column(
                "submitted_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )

    if "alerts" not in existing:
        op.create_table(
            "alerts",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("hazard_type", sa.String(), nullable=False),
            sa.Column("severity", sa.String(), nullable=True),
            sa.Column("title", sa.String(), nullable=True),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("source", sa.String(), nullable=True),
            sa.Column("latitude", sa.Float(), nullable=True),
            sa.Column("longitude", sa.Float(), nullable=True),
            sa.Column(
                "issued_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        )

    if "alert_subscriptions" not in existing:
        op.create_table(
            "alert_subscriptions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("session_id", sa.String(), nullable=False, server_default="default"),
            sa.Column("push_token", sa.String(), nullable=True),
            sa.Column("latitude", sa.Float(), nullable=True),
            sa.Column("longitude", sa.Float(), nullable=True),
            sa.Column("radius_km", sa.Float(), nullable=False, server_default="50"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )

    if "users" not in existing:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("external_id", sa.String(), nullable=True, unique=True),
            sa.Column("display_name", sa.String(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )


def downgrade() -> None:
    existing = _existing_tables()

    for table_name in ("users", "alert_subscriptions", "alerts", "feedback", "sessions"):
        if table_name in existing:
            op.drop_table(table_name)

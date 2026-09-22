"""
ORCA / NeerMitra — Alembic environment.

Deliberately reuses the app's own `DATABASE_URL` resolution
(`server.src.config.settings` + the postgres:// -> postgresql+psycopg://
normalization in `server.src.config.database`) so the same connection
string logic is never duplicated or allowed to drift between the running
app and its migrations.
"""

import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Make the repo root importable (mirrors server/src/app.py's own sys.path setup)
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from server.src.config.database import NORMALIZED_DATABASE_URL  # noqa: E402
from server.src.models.base import Base  # noqa: E402
import server.src.models  # noqa: E402,F401  (registers all models on Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

if NORMALIZED_DATABASE_URL:
    config.set_main_option("sqlalchemy.url", NORMALIZED_DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

import logging

from sqlalchemy import create_engine
from server.src.config.settings import DATABASE_URL

logger = logging.getLogger(__name__)

engine = None
if DATABASE_URL:
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5},
        )
        logger.info(
            "SQLAlchemy engine created backend=%s driver=%s",
            engine.url.get_backend_name(),
            engine.url.get_driver_name(),
        )
    except Exception:
        logger.exception("SQLAlchemy engine creation failed")
        engine = None


def get_db_engine():
    global engine

    if engine is None and DATABASE_URL:
        try:
            engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 5},
            )
            logger.info(
                "SQLAlchemy engine created backend=%s driver=%s",
                engine.url.get_backend_name(),
                engine.url.get_driver_name(),
            )
        except Exception:
            logger.exception("SQLAlchemy engine creation failed")
            engine = None

    return engine

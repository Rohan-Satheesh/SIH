import logging

from sqlalchemy import create_engine
from server.src.config.settings import DATABASE_URL

logger = logging.getLogger(__name__)


def _log_database_url_diagnostics(database_url):
    is_none = database_url is None
    scheme = (
        database_url.split("://", 1)[0]
        if isinstance(database_url, str) and "://" in database_url
        else ""
    )
    logger.info(
        "DATABASE_URL diagnostics none=%s length=%s scheme=%s "
        "starts_with_psycopg=%s",
        is_none,
        len(database_url) if isinstance(database_url, str) else None,
        scheme,
        isinstance(database_url, str)
        and database_url.startswith("postgresql+psycopg://"),
    )


def _normalize_database_url(database_url):
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg://" + database_url[len("postgres://"):]

    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url[len("postgresql://"):]

    return database_url


NORMALIZED_DATABASE_URL = (
    _normalize_database_url(DATABASE_URL)
    if DATABASE_URL
    else DATABASE_URL
)

engine = None
if DATABASE_URL:
    try:
        _log_database_url_diagnostics(DATABASE_URL)
        engine = create_engine(
            NORMALIZED_DATABASE_URL,
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

    if engine is None and NORMALIZED_DATABASE_URL:
        try:
            _log_database_url_diagnostics(DATABASE_URL)
            engine = create_engine(
                NORMALIZED_DATABASE_URL,
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

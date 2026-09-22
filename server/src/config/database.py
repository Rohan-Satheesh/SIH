import logging
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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


_session_factory = None
_session_factory_engine = None


def get_sessionmaker():
    """
    Return a `sessionmaker` bound to the current engine, or None if no
    database is configured/reachable. Rebuilds the factory if the engine
    instance has changed (e.g. after a lazy re-connect in get_db_engine()).
    """
    global _session_factory, _session_factory_engine

    current_engine = get_db_engine()
    if current_engine is None:
        return None

    if _session_factory is None or _session_factory_engine is not current_engine:
        _session_factory = sessionmaker(
            bind=current_engine, autoflush=False, autocommit=False, future=True
        )
        _session_factory_engine = current_engine

    return _session_factory


@contextmanager
def get_db_session():
    """
    Context manager yielding a SQLAlchemy Session, or None when no database
    is configured/reachable. Callers MUST check for None and fall back to
    an in-memory/alternate code path — this never raises for connectivity
    reasons, so a missing/unreachable database can never break a request.

    Usage:
        with get_db_session() as db:
            if db is None:
                ...fallback...
                return
            db.add(SomeModel(...))
    """
    factory = get_sessionmaker()
    if factory is None:
        yield None
        return

    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """
    Best-effort schema bootstrap: creates any tables registered on
    `Base.metadata` that don't already exist (SQLAlchemy's `create_all` is
    idempotent — it never touches existing tables/columns).

    This is a safety net, not a replacement for Alembic. It exists so the
    app keeps working immediately after deploy even before `alembic upgrade
    head` has been run manually against the production database. Alembic
    remains the source of truth for future schema changes.

    Safe to call on every startup: no-ops quietly if there is no database
    configured or reachable.
    """
    current_engine = get_db_engine()
    if current_engine is None:
        logger.info("init_db: no database configured/reachable, skipping schema bootstrap.")
        return

    try:
        from server.src.models.base import Base
        import server.src.models  # noqa: F401  (registers all model classes on Base.metadata)

        Base.metadata.create_all(bind=current_engine, checkfirst=True)
        logger.info("init_db: schema bootstrap complete (create_all, checkfirst=True).")
    except Exception:
        logger.exception("init_db: schema bootstrap failed; continuing without it.")

from sqlalchemy import create_engine
from server.src.config.settings import DATABASE_URL

engine = None
if DATABASE_URL:
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5},
        )
    except Exception:
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
        except Exception:
            engine = None

    return engine

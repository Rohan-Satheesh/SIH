import socket
from urllib.parse import urlparse
from sqlalchemy import create_engine
from server.src.config.settings import DATABASE_URL

def is_db_available() -> bool:
    """Probes whether local PostgreSQL/PostGIS port is accepting connections."""
    try:
        parsed = urlparse(DATABASE_URL)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 5432
        with socket.create_connection((host, port), timeout=0.8):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

engine = None
if DATABASE_URL and is_db_available():
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 1})
    except Exception:
        engine = None

def get_db_engine():
    global engine
    if engine is None and is_db_available():
        try:
            engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 1})
        except Exception:
            engine = None
    return engine

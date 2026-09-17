"""
Database Writer & Dataset Freshness Tracker (CHUNK_ID: R4-C08)
--------------------------------------------------------------
Role: Role 4 (Data Pipeline Engineer)
Target: pipeline/storage/db_writer.py
Prerequisite: [R4-C01] (pipeline.config, pipeline.storage.b2_uploader)

Maintains the `data_freshness` PostgreSQL table tracking:
- dataset_name (unique identifier per data source)
- last_updated (UTC timestamp)
- status ('SUCCESS', 'FAILED', 'RUNNING')
- record_count (processed features or records)
- file_size_bytes (byte size of ingested/processed asset)
- error_message & error_traceback (full diagnostic stack trace upon failure)
- source_info & extra_metadata (JSON metadata)

Provides idempotent parameterized updates, connection management with reconnection,
context manager for automatic failure catching without swallowing exceptions,
and exposure to backend REST API endpoints.
"""

import os
import sys
import json
import logging
import sqlite3
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from contextlib import contextmanager

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import DatabaseConfig

# Try importing psycopg2
try:
    import psycopg2
    from psycopg2 import sql, extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("db_writer")


class DBWriter:
    """
    Manages PostgreSQL database interactions, table initialization,
    and dataset freshness tracking for the NeerMitra data pipeline.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        dbname: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        mock_mode: bool = False
    ):
        self.host = host or DatabaseConfig.HOST
        self.port = port or DatabaseConfig.PORT
        self.dbname = dbname or DatabaseConfig.DB_NAME
        self.user = user or DatabaseConfig.USER
        self.password = password if password is not None else DatabaseConfig.PASSWORD
        self.mock_mode = mock_mode

        self.sqlite_db_path = Path(DatabaseConfig.SQLITE_FALLBACK_PATH)
        self.is_postgres = False

        if not self.mock_mode and HAS_PSYCOPG2:
            self.is_postgres = self._test_postgres_connection()

        if not self.is_postgres:
            if not self.mock_mode:
                logger.warning(
                    f"PostgreSQL connection to {self.host}:{self.port}/{self.dbname} could not be established. "
                    f"Using local SQLite fallback at '{self.sqlite_db_path}'."
                )
            self.mock_mode = True
            self.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)

        self.init_schema()

    def _test_postgres_connection(self) -> bool:
        """Verify PostgreSQL connectivity."""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                connect_timeout=3
            )
            conn.close()
            logger.info(f"Connected to PostgreSQL database '{self.dbname}' at {self.host}:{self.port}.")
            return True
        except Exception as e:
            logger.debug(f"PostgreSQL probe failed: {e}")
            return False

    def _get_connection(self):
        """Get database connection depending on mode."""
        if self.is_postgres:
            return psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                connect_timeout=5
            )
        else:
            conn = sqlite3.connect(str(self.sqlite_db_path), timeout=10)
            conn.row_factory = sqlite3.Row
            return conn

    def init_schema(self) -> bool:
        """
        Create `data_freshness` table and indexes idempotently.
        """
        if self.is_postgres:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS data_freshness (
                id SERIAL PRIMARY KEY,
                dataset_name VARCHAR(128) UNIQUE NOT NULL,
                last_updated TIMESTAMPTZ NOT NULL,
                status VARCHAR(32) NOT NULL,
                record_count INTEGER DEFAULT 0,
                file_size_bytes BIGINT DEFAULT 0,
                error_message TEXT,
                error_traceback TEXT,
                source_info JSONB,
                extra_metadata JSONB,
                created_at TIMESTAMPTZ DEFAULT (NOW() AT TIME ZONE 'UTC')
            );
            CREATE INDEX IF NOT EXISTS idx_data_freshness_dataset ON data_freshness(dataset_name);
            CREATE INDEX IF NOT EXISTS idx_data_freshness_status ON data_freshness(status);
            """
            try:
                with self._get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(create_table_sql)
                    conn.commit()
                logger.info("PostgreSQL table 'data_freshness' verified/created.")
                return True
            except Exception as e:
                logger.error(f"Error initializing PostgreSQL schema: {e}")
                raise
        else:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS data_freshness (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_name TEXT UNIQUE NOT NULL,
                last_updated TEXT NOT NULL,
                status TEXT NOT NULL,
                record_count INTEGER DEFAULT 0,
                file_size_bytes INTEGER DEFAULT 0,
                error_message TEXT,
                error_traceback TEXT,
                source_info TEXT,
                extra_metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_data_freshness_dataset ON data_freshness(dataset_name);
            CREATE INDEX IF NOT EXISTS idx_data_freshness_status ON data_freshness(status);
            """
            try:
                conn = self._get_connection()
                cur = conn.cursor()
                cur.executescript(create_table_sql)
                conn.commit()
                conn.close()
                logger.info("SQLite table 'data_freshness' verified/created.")
                return True
            except Exception as e:
                logger.error(f"Error initializing SQLite schema: {e}")
                raise

    def record_success(
        self,
        dataset_name: str,
        record_count: int = 0,
        file_size_bytes: int = 0,
        source_info: Optional[Dict[str, Any]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        last_updated: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Record a successful ingestion job run in data_freshness.
        Idempotent: updates existing record if dataset_name exists.
        """
        ts = last_updated or datetime.now(timezone.utc)
        status = "SUCCESS"

        source_info_json = json.dumps(source_info) if source_info else None
        extra_metadata_json = json.dumps(extra_metadata) if extra_metadata else None

        if self.is_postgres:
            upsert_sql = """
            INSERT INTO data_freshness (
                dataset_name, last_updated, status, record_count, file_size_bytes,
                error_message, error_traceback, source_info, extra_metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (dataset_name) DO UPDATE SET
                last_updated = EXCLUDED.last_updated,
                status = EXCLUDED.status,
                record_count = EXCLUDED.record_count,
                file_size_bytes = EXCLUDED.file_size_bytes,
                error_message = NULL,
                error_traceback = NULL,
                source_info = EXCLUDED.source_info,
                extra_metadata = EXCLUDED.extra_metadata;
            """
            params = (
                dataset_name, ts, status, record_count, file_size_bytes,
                None, None, source_info_json, extra_metadata_json
            )
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(upsert_sql, params)
                conn.commit()
        else:
            upsert_sql = """
            INSERT INTO data_freshness (
                dataset_name, last_updated, status, record_count, file_size_bytes,
                error_message, error_traceback, source_info, extra_metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(dataset_name) DO UPDATE SET
                last_updated = excluded.last_updated,
                status = excluded.status,
                record_count = excluded.record_count,
                file_size_bytes = excluded.file_size_bytes,
                error_message = NULL,
                error_traceback = NULL,
                source_info = excluded.source_info,
                extra_metadata = excluded.extra_metadata;
            """
            params = (
                dataset_name, ts.isoformat(), status, record_count, file_size_bytes,
                None, None, source_info_json, extra_metadata_json
            )
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(upsert_sql, params)
            conn.commit()
            conn.close()

        logger.info(f"Recorded freshness SUCCESS for '{dataset_name}' ({record_count} records, {file_size_bytes} bytes).")
        return {
            "dataset_name": dataset_name,
            "last_updated": ts.isoformat(),
            "status": status,
            "record_count": record_count,
            "file_size_bytes": file_size_bytes
        }

    def record_failure(
        self,
        dataset_name: str,
        error: Union[Exception, str],
        error_trace: Optional[str] = None,
        source_info: Optional[Dict[str, Any]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Record a failed ingestion attempt with error message and full stack trace.
        Idempotent: updates existing record for dataset_name.
        """
        ts = timestamp or datetime.now(timezone.utc)
        status = "FAILED"

        error_message = str(error)
        if error_trace is None:
            if isinstance(error, Exception):
                error_trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            else:
                error_trace = "".join(traceback.format_stack())

        source_info_json = json.dumps(source_info) if source_info else None
        extra_metadata_json = json.dumps(extra_metadata) if extra_metadata else None

        if self.is_postgres:
            upsert_sql = """
            INSERT INTO data_freshness (
                dataset_name, last_updated, status, record_count, file_size_bytes,
                error_message, error_traceback, source_info, extra_metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (dataset_name) DO UPDATE SET
                last_updated = EXCLUDED.last_updated,
                status = EXCLUDED.status,
                error_message = EXCLUDED.error_message,
                error_traceback = EXCLUDED.error_traceback,
                source_info = COALESCE(EXCLUDED.source_info, data_freshness.source_info),
                extra_metadata = COALESCE(EXCLUDED.extra_metadata, data_freshness.extra_metadata);
            """
            params = (
                dataset_name, ts, status, 0, 0,
                error_message, error_trace, source_info_json, extra_metadata_json
            )
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(upsert_sql, params)
                conn.commit()
        else:
            upsert_sql = """
            INSERT INTO data_freshness (
                dataset_name, last_updated, status, record_count, file_size_bytes,
                error_message, error_traceback, source_info, extra_metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(dataset_name) DO UPDATE SET
                last_updated = excluded.last_updated,
                status = excluded.status,
                error_message = excluded.error_message,
                error_traceback = excluded.error_traceback,
                source_info = COALESCE(excluded.source_info, data_freshness.source_info),
                extra_metadata = COALESCE(excluded.extra_metadata, data_freshness.extra_metadata);
            """
            params = (
                dataset_name, ts.isoformat(), status, 0, 0,
                error_message, error_trace, source_info_json, extra_metadata_json
            )
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(upsert_sql, params)
            conn.commit()
            conn.close()

        logger.warning(f"Recorded freshness FAILED for '{dataset_name}': {error_message}")
        return {
            "dataset_name": dataset_name,
            "last_updated": ts.isoformat(),
            "status": status,
            "error_message": error_message,
            "error_traceback": error_trace
        }

    def get_freshness(self, dataset_name: str) -> Optional[Dict[str, Any]]:
        """
        Get freshness record for a specific dataset.
        """
        if self.is_postgres:
            query = """
            SELECT dataset_name, last_updated, status, record_count, file_size_bytes,
                   error_message, error_traceback, source_info, extra_metadata
            FROM data_freshness
            WHERE dataset_name = %s;
            """
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (dataset_name,))
                    row = cur.fetchone()
                    if not row:
                        return None
                    return self._row_to_dict(row, [
                        "dataset_name", "last_updated", "status", "record_count", "file_size_bytes",
                        "error_message", "error_traceback", "source_info", "extra_metadata"
                    ])
        else:
            query = """
            SELECT dataset_name, last_updated, status, record_count, file_size_bytes,
                   error_message, error_traceback, source_info, extra_metadata
            FROM data_freshness
            WHERE dataset_name = ?;
            """
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(query, (dataset_name,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return None
            return self._sqlite_row_to_dict(row)

    def get_all_freshness(self) -> List[Dict[str, Any]]:
        """
        Get all dataset freshness records, sorted by last_updated descending.
        """
        if self.is_postgres:
            query = """
            SELECT dataset_name, last_updated, status, record_count, file_size_bytes,
                   error_message, error_traceback, source_info, extra_metadata
            FROM data_freshness
            ORDER BY last_updated DESC;
            """
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    rows = cur.fetchall()
                    cols = [
                        "dataset_name", "last_updated", "status", "record_count", "file_size_bytes",
                        "error_message", "error_traceback", "source_info", "extra_metadata"
                    ]
                    return [self._row_to_dict(r, cols) for r in rows]
        else:
            query = """
            SELECT dataset_name, last_updated, status, record_count, file_size_bytes,
                   error_message, error_traceback, source_info, extra_metadata
            FROM data_freshness
            ORDER BY last_updated DESC;
            """
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            conn.close()
            return [self._sqlite_row_to_dict(r) for r in rows]

    def _row_to_dict(self, row: tuple, cols: List[str]) -> Dict[str, Any]:
        """Convert postgres row to formatted dict."""
        d = dict(zip(cols, row))
        if isinstance(d.get("last_updated"), datetime):
            d["last_updated"] = d["last_updated"].isoformat()
        if isinstance(d.get("source_info"), str):
            try:
                d["source_info"] = json.loads(d["source_info"])
            except Exception:
                pass
        if isinstance(d.get("extra_metadata"), str):
            try:
                d["extra_metadata"] = json.loads(d["extra_metadata"])
            except Exception:
                pass
        return d

    def _sqlite_row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert sqlite row to formatted dict."""
        d = dict(row)
        for field in ["source_info", "extra_metadata"]:
            if d.get(field):
                try:
                    d[field] = json.loads(d[field])
                except Exception:
                    pass
        return d

    @contextmanager
    def track_ingestion(
        self,
        dataset_name: str,
        source_info: Optional[Dict[str, Any]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for automatic execution tracking:
        - Automatically records SUCCESS if block completes.
        - Automatically records FAILED with stack trace if an exception is raised.
        - DOES NOT swallow exceptions (re-raises after logging).
        """
        class IngestionTracker:
            def __init__(self):
                self.record_count = 0
                self.file_size_bytes = 0
                self.custom_source_info = source_info or {}
                self.custom_metadata = extra_metadata or {}

            def set_results(self, count: int = 0, size_bytes: int = 0, **kwargs):
                self.record_count = count
                self.file_size_bytes = size_bytes
                self.custom_metadata.update(kwargs)

        tracker = IngestionTracker()
        try:
            yield tracker
            self.record_success(
                dataset_name=dataset_name,
                record_count=tracker.record_count,
                file_size_bytes=tracker.file_size_bytes,
                source_info=tracker.custom_source_info,
                extra_metadata=tracker.custom_metadata
            )
        except Exception as err:
            self.record_failure(
                dataset_name=dataset_name,
                error=err,
                source_info=tracker.custom_source_info,
                extra_metadata=tracker.custom_metadata
            )
            raise  # Re-raise without swallowing


def run_demo():
    """Run interactive demonstration of DBWriter freshness tracker with real PostgreSQL."""
    print("=" * 70)
    print("DEMO: DATASET FRESHNESS TRACKER & HEALTH LOGGER (CHUNK_ID: R4-C08)")
    print("=" * 70)

    writer = DBWriter()
    print(f"Backend Engine: {'PostgreSQL (Production)' if writer.is_postgres else 'SQLite (Simulation)'}")

    # 1. Successful Ingestion Record
    print("\n1. Recording successful ingestion for 'copernicus_sst'...")
    res = writer.record_success(
        dataset_name="copernicus_sst",
        record_count=9600,
        file_size_bytes=3701848,
        source_info={"provider": "CMEMS", "product": "METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2"},
        extra_metadata={"interpolated": True, "b2_key": "processed/tiles/sst/copernicus/2026-09-06.geojson"}
    )
    print(f"   - Stored record: {res}")

    # 2. Query Freshness
    print("\n2. Querying freshness for 'copernicus_sst'...")
    rec = writer.get_freshness("copernicus_sst")
    print(f"   - Retrieved status : {rec['status']}")
    print(f"   - Last updated     : {rec['last_updated']}")
    print(f"   - Record count     : {rec['record_count']}")
    print(f"   - File size        : {rec['file_size_bytes']} bytes")

    # 3. Controlled Failure Test
    print("\n3. Testing controlled failure logging for 'noaa_forecast'...")
    try:
        with writer.track_ingestion("noaa_forecast", source_info={"url": "https://api.tidesandcurrents.noaa.gov"}):
            raise ConnectionError("Simulated upstream NOAA NOMADS connection timeout (504 Gateway Timeout)")
    except ConnectionError as e:
        print(f"   - Caught expected simulated error: {e}")

    failed_rec = writer.get_freshness("noaa_forecast")
    print(f"   - Failed record status : {failed_rec['status']}")
    print(f"   - Error message        : {failed_rec['error_message']}")
    print(f"   - Stack trace logged   : {bool(failed_rec['error_traceback'])}")

    # 4. Idempotency Test
    print("\n4. Testing idempotent update for 'copernicus_sst'...")
    writer.record_success(
        dataset_name="copernicus_sst",
        record_count=9650,
        file_size_bytes=3705000
    )
    updated_rec = writer.get_freshness("copernicus_sst")
    print(f"   - Updated record count : {updated_rec['record_count']} (was 9600)")

    # 5. List all freshness
    print("\n5. Listing all tracked dataset freshness records:")
    all_recs = writer.get_all_freshness()
    for r in all_recs:
        print(f"   - {r['dataset_name']:<20}: {r['status']:<8} | Updated: {r['last_updated']} | Records: {r['record_count']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()

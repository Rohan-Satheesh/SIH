import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv()
env_backend = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", ".env")
if os.path.exists(env_backend):
    load_dotenv(dotenv_path=env_backend)

class B2Config:

    """Configuration container for Backblaze B2 Infrastructure."""
    
    # Backblaze B2 API Credentials & Endpoint Settings
    KEY_ID: str = os.getenv("B2_APPLICATION_KEY_ID") or os.getenv("B2_KEY_ID") or ""
    APPLICATION_KEY: str = os.getenv("B2_APPLICATION_KEY") or os.getenv("B2_APP_KEY") or ""
    BUCKET_NAME: str = os.getenv("B2_BUCKET_NAME", "orca-marine-data")
    ENDPOINT_URL: str = os.getenv(
        "B2_ENDPOINT_URL", 
        "https://s3.us-west-004.backblazeb2.com"
    )
    REGION_NAME: str = os.getenv("B2_REGION_NAME", "us-west-004")
    # Directory Key Structure Requirements (CHUNK_ID: R4-C01 / Image 5)

    DIRECTORY_KEYS: List[str] = [
        "satellite/sst/copernicus/",
        "satellite/sst/nasa-modis/",
        "satellite/chlorophyll/",
        "satellite/currents/",
        "weather/imd/",
        "weather/noaa/",
        "tides/",
        "advisories/pfz/",
        "advisories/osf/",
        "boundaries/",
        "processed/risk-maps/",
        "processed/trends/",
        "processed/tiles/",
        "staging/"
    ]
    # Individual Key Constants for Code References
    KEY_SATELLITE_SST_COPERNICUS: str = "satellite/sst/copernicus/"
    KEY_SATELLITE_SST_NASA_MODIS: str = "satellite/sst/nasa-modis/"
    KEY_SATELLITE_CHLOROPHYLL: str = "satellite/chlorophyll/"
    KEY_SATELLITE_CURRENTS: str = "satellite/currents/"
    KEY_WEATHER_IMD: str = "weather/imd/"
    KEY_WEATHER_NOAA: str = "weather/noaa/"
    KEY_TIDES: str = "tides/"
    KEY_ADVISORIES_PFZ: str = "advisories/pfz/"
    KEY_ADVISORIES_OSF: str = "advisories/osf/"
    KEY_BOUNDARIES: str = "boundaries/"
    KEY_PROCESSED_RISK_MAPS: str = "processed/risk-maps/"
    KEY_PROCESSED_TRENDS: str = "processed/trends/"
    KEY_PROCESSED_TILES: str = "processed/tiles/"
    KEY_STAGING: str = "staging/"
    # Lifecycle Rule Configurations
    # Raw temporary staging files auto-deleted after 30 days
    STAGING_LIFECYCLE_DAYS: int = 30
    STAGING_LIFECYCLE_RULE: Dict[str, Any] = {
        "fileNamePrefix": "staging/",
        "daysDaysAfterUploadingToDeletion": 30,
        "description": "Auto-delete raw temporary staging files after 30 days"
    }
    @classmethod
    def is_configured(cls) -> bool:
        """Check if valid B2 API credentials are provided in the environment."""
        return bool(cls.KEY_ID and cls.APPLICATION_KEY)
    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """Return non-sensitive configuration summary."""
        return {
            "bucket_name": cls.BUCKET_NAME,
            "endpoint_url": cls.ENDPOINT_URL,
            "region_name": cls.REGION_NAME,
            "configured": cls.is_configured(),
            "directory_count": len(cls.DIRECTORY_KEYS),
            "directories": cls.DIRECTORY_KEYS,
            "staging_lifecycle_days": cls.STAGING_LIFECYCLE_DAYS,
        }


class CopernicusConfig:
    """Configuration container for Copernicus Marine Service API & Ingestion."""

    USERNAME: str = os.getenv("COPERNICUS_USERNAME") or os.getenv("COPERNICUS_MARINE_USERNAME") or os.getenv("COPERNICUS_USER") or ""
    PASSWORD: str = os.getenv("COPERNICUS_PASSWORD") or os.getenv("COPERNICUS_MARINE_PASSWORD") or os.getenv("COPERNICUS_PASS") or ""

    # Indian Ocean Bounding Box: 5°N to 25°N, 65°E to 95°E (CHUNK_ID: R4-C02)
    MIN_LATITUDE: float = 5.0
    MAX_LATITUDE: float = 25.0
    MIN_LONGITUDE: float = 65.0
    MAX_LONGITUDE: float = 95.0

    BOUNDING_BOX: Dict[str, float] = {
        "minimum_latitude": MIN_LATITUDE,
        "maximum_latitude": MAX_LATITUDE,
        "minimum_longitude": MIN_LONGITUDE,
        "maximum_longitude": MAX_LONGITUDE,
    }

    # Standard Copernicus Marine Product IDs
    # Sea Surface Temperature (SST) - L4 Daily Analysis
    DATASET_SST: str = os.getenv(
        "COPERNICUS_DATASET_SST",
        "METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2"
    )
    # Ocean Colour / Chlorophyll - L4 Daily Analysis (Gap-free 4km)
    DATASET_CHLOROPHYLL: str = os.getenv(
        "COPERNICUS_DATASET_CHLOROPHYLL",
        "cmems_obs-oc_glo_bgc-plankton_nrt_l4-gapfree-multi-4km_P1D"
    )
    # Ocean Physics / Currents - Global Analysis and Forecast (Surface currents uo, vo)
    DATASET_CURRENTS: str = os.getenv(
        "COPERNICUS_DATASET_CURRENTS",
        "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m"
    )

    # Variables for extraction
    VARIABLES_SST: List[str] = ["analysed_sst"]
    VARIABLES_CHLOROPHYLL: List[str] = ["CHL"]
    VARIABLES_CURRENTS: List[str] = ["uo", "vo"]

    # Target B2 storage paths
    B2_SST_TEMPLATE: str = "satellite/sst/copernicus/{date}.nc"
    B2_CHLOROPHYLL_TEMPLATE: str = "satellite/chlorophyll/{date}.nc"
    B2_CURRENTS_TEMPLATE: str = "satellite/currents/{date}.nc"

    @classmethod
    def is_configured(cls) -> bool:
        """Check if Copernicus Marine credentials are provided."""
        return bool(cls.USERNAME and cls.PASSWORD)

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """Return configuration summary without sensitive credentials."""
        return {
            "configured": cls.is_configured(),
            "username_set": bool(cls.USERNAME),
            "bounding_box": cls.BOUNDING_BOX,
            "datasets": {
                "sst": cls.DATASET_SST,
                "chlorophyll": cls.DATASET_CHLOROPHYLL,
                "currents": cls.DATASET_CURRENTS,
            },
        }


class NasaGeeConfig:
    """Configuration container for NASA GEE MODIS Satellite Data Ingestion (CHUNK_ID: R4-C03)."""

    PROJECT_ID: str = (
        os.getenv("GEE_PROJECT_ID")
        or os.getenv("EARTHENGINE_PROJECT")
        or "orca-508605"
    )

    # Indian Ocean / Indian EEZ Bounding Box: 5°N to 25°N, 65°E to 95°E
    MIN_LATITUDE: float = 5.0
    MAX_LATITUDE: float = 25.0
    MIN_LONGITUDE: float = 65.0
    MAX_LONGITUDE: float = 95.0

    BOUNDING_BOX: Dict[str, float] = {
        "minimum_latitude": MIN_LATITUDE,
        "maximum_latitude": MAX_LATITUDE,
        "minimum_longitude": MIN_LONGITUDE,
        "maximum_longitude": MAX_LONGITUDE,
    }

    # NASA GEE MODIS-Aqua L3 SMI Collection ID
    COLLECTION_ID: str = "NASA/OCEANDATA/MODIS-Aqua/L3SMI"

    # Bands
    BAND_CHLOROPHYLL: str = "chlor_a"
    BAND_SST: str = "sst"

    # Target B2 storage paths (GeoTIFF)
    B2_CHLOROPHYLL_TEMPLATE: str = "satellite/chlorophyll/nasa/{date}.tif"
    B2_SST_TEMPLATE: str = "satellite/sst/nasa-modis/{date}.tif"

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """Return non-sensitive configuration summary."""
        return {
            "project_id": cls.PROJECT_ID,
            "collection_id": cls.COLLECTION_ID,
            "bounding_box": cls.BOUNDING_BOX,
            "bands": {
                "chlorophyll": cls.BAND_CHLOROPHYLL,
                "sst": cls.BAND_SST,
            },
            "b2_templates": {
                "chlorophyll": cls.B2_CHLOROPHYLL_TEMPLATE,
                "sst": cls.B2_SST_TEMPLATE,
            }
        }


class NoaaConfig:
    """Configuration container for NOAA Tides & Weather Data Ingestion (CHUNK_ID: R4-C04)."""

    # NOAA CO-OPS REST API endpoints
    COOPS_API_URL: str = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    COOPS_STATIONS_URL: str = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/tidepredstations.json"

    # NOAA GFS Wave / NOMADS & Marine Forecast endpoints
    NOMADS_GFS_WAVE_URL: str = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfswave.pl"
    MARINE_WAVE_API_URL: str = "https://marine-api.open-meteo.com/v1/marine"

    # Indian Ocean / Indian EEZ Bounding Box: 5°N to 25°N, 65°E to 95°E
    MIN_LATITUDE: float = 5.0
    MAX_LATITUDE: float = 25.0
    MIN_LONGITUDE: float = 65.0
    MAX_LONGITUDE: float = 95.0

    BOUNDING_BOX: Dict[str, float] = {
        "minimum_latitude": MIN_LATITUDE,
        "maximum_latitude": MAX_LATITUDE,
        "minimum_longitude": MIN_LONGITUDE,
        "maximum_longitude": MAX_LONGITUDE,
    }

    # Verified NOAA CO-OPS Stations & Major Indian Coastal Ports
    COOPS_STATIONS: List[Dict[str, Any]] = [
        {"id": "2431000", "name": "Diego Garcia (Indian Ocean)", "latitude": -7.29, "longitude": 72.39}
    ]

    INDIAN_PORTS: List[Dict[str, Any]] = [
        {"key": "mumbai", "name": "Mumbai Port", "latitude": 18.96, "longitude": 72.82},
        {"key": "cochin", "name": "Cochin / Kochi Port", "latitude": 9.96, "longitude": 76.26},
        {"key": "chennai", "name": "Chennai Port", "latitude": 13.08, "longitude": 80.29},
        {"key": "visakhapatnam", "name": "Visakhapatnam Port", "latitude": 17.68, "longitude": 83.22},
        {"key": "kandla", "name": "Kandla Port", "latitude": 23.00, "longitude": 70.22},
        {"key": "mormugao", "name": "Mormugao Port (Goa)", "latitude": 15.41, "longitude": 73.80},
        {"key": "mangalore", "name": "New Mangalore Port", "latitude": 12.92, "longitude": 74.82},
        {"key": "paradip", "name": "Paradip Port", "latitude": 20.26, "longitude": 86.67},
        {"key": "haldia", "name": "Haldia / Kolkata Port", "latitude": 22.02, "longitude": 88.06},
        {"key": "tuticorin", "name": "V.O.C Port (Tuticorin)", "latitude": 8.75, "longitude": 78.18},
    ]

    # Target B2 storage path template
    B2_NOAA_TEMPLATE: str = "weather/noaa/{date}.json"

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """Return non-sensitive configuration summary."""
        return {
            "coops_api_url": cls.COOPS_API_URL,
            "nomads_gfs_wave_url": cls.NOMADS_GFS_WAVE_URL,
            "bounding_box": cls.BOUNDING_BOX,
            "coops_stations": cls.COOPS_STATIONS,
            "indian_ports": [p["name"] for p in cls.INDIAN_PORTS],
            "b2_template": cls.B2_NOAA_TEMPLATE,
        }


class IncoisConfig:
    """Configuration container for INCOIS Advisory Web Scraper (CHUNK_ID: R4-C05)."""

    RSMCND_BASE: str = "https://rsmcnewdelhi.imd.gov.in"
    RSMCND_FISHERMEN_URL: str = "https://rsmcnewdelhi.imd.gov.in/fishermen-warning.php"
    RSMCND_COASTAL_URL: str = "https://rsmcnewdelhi.imd.gov.in/coastal-weather-bulletin.php"
    INCOIS_FORECAST_URL: str = "https://incois.gov.in/site/forecast.jsp"
    IMD_CAP_RSS_URL: str = "https://cap-sources.s3.amazonaws.com/in-imd-en/rss.xml"

    B2_PFZ_TEMPLATE: str = "advisories/pfz/{date}.json"
    B2_OSF_TEMPLATE: str = "advisories/osf/{date}.json"

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        return {
            "rsmcnd_fishermen_url": cls.RSMCND_FISHERMEN_URL,
            "rsmcnd_coastal_url": cls.RSMCND_COASTAL_URL,
            "incois_forecast_url": cls.INCOIS_FORECAST_URL,
            "cap_rss_url": cls.IMD_CAP_RSS_URL,
            "b2_pfz_template": cls.B2_PFZ_TEMPLATE,
            "b2_osf_template": cls.B2_OSF_TEMPLATE,
        }


class ImdConfig:
    """Configuration container for IMD Marine Warning Scraper (CHUNK_ID: R4-C06)."""

    RSMCND_BASE: str = "https://rsmcnewdelhi.imd.gov.in"
    IMD_CAP_RSS_URL: str = "https://cap-sources.s3.amazonaws.com/in-imd-en/rss.xml"
    B2_IMD_TEMPLATE: str = "weather/imd/{date}.json"

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        return {
            "rsmcnd_base": cls.RSMCND_BASE,
            "cap_rss_url": cls.IMD_CAP_RSS_URL,
            "b2_imd_template": cls.B2_IMD_TEMPLATE,
        }


class DatabaseConfig:
    """Configuration container for PostgreSQL Database & Freshness Tracking."""

    HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    DB_NAME: str = os.getenv("POSTGRES_DB", "orca")
    USER: str = os.getenv("POSTGRES_USER", "orca")
    PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "orca_dev")

    SQLITE_FALLBACK_PATH: str = os.getenv(
        "DB_SQLITE_FALLBACK",
        str(PROJECT_ROOT / ".mock_db" / "orca.db")
    )

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.HOST and cls.DB_NAME and cls.USER and cls.PASSWORD)

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        return {
            "host": cls.HOST,
            "port": cls.PORT,
            "database": cls.DB_NAME,
            "user": cls.USER,
            "password_set": bool(cls.PASSWORD),
            "sqlite_fallback": cls.SQLITE_FALLBACK_PATH
        }


class SchedulerConfig:
    """Configuration container for Automated ETL Scheduler Engine (CHUNK_ID: R4-C09)."""

    MAX_RETRIES: int = int(os.getenv("PIPELINE_MAX_RETRIES", "3"))
    BACKOFF_BASE_SEC: float = float(os.getenv("PIPELINE_BACKOFF_BASE_SEC", "5.0"))
    TIMEZONE: str = os.getenv("PIPELINE_TIMEZONE", "UTC")

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        return {
            "max_retries": cls.MAX_RETRIES,
            "backoff_base_sec": cls.BACKOFF_BASE_SEC,
            "timezone": cls.TIMEZONE,
        }


class ChromaConfig:
    """Configuration container for RAG Advisory Vector Store (CHUNK_ID: R4-C10)."""

    PERSIST_DIR: str = os.getenv(
        "CHROMA_PERSIST_DIR",
        str(PROJECT_ROOT / ".chroma_db") if "PROJECT_ROOT" in globals() else ".chroma_db"
    )
    COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "marine_advisories")
    EMBEDDING_MODEL: str = os.getenv(
        "CHROMA_EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        return {
            "persist_dir": cls.PERSIST_DIR,
            "collection_name": cls.COLLECTION_NAME,
            "embedding_model": cls.EMBEDDING_MODEL,
            "chunk_size": cls.CHUNK_SIZE,
            "chunk_overlap": cls.CHUNK_OVERLAP,
        }





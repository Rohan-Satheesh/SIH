"""
Automated ETL Scheduler Engine Configuration (CHUNK_ID: R4-C09)
----------------------------------------------------------------
Role: Role 4 (Data Pipeline Engineer)
Target: pipeline/schedulers/cron_config.py
Prerequisites: [R4-C02], [R4-C03], [R4-C04], [R4-C05], [R4-C06]

Configures APScheduler cron schedules and exponential backoff retry policies for:
1. Copernicus Marine: every 6 hours
2. NASA GEE MODIS: daily at 02:00 UTC
3. NOAA Weather & Tides: every 3 hours
4. INCOIS PFZ/OSF Scraper: every 12 hours
5. IMD Marine Warnings: every 6 hours
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import os


@dataclass
class RetryConfig:
    """Retry policy for ingestion jobs."""
    max_attempts: int = 3
    initial_backoff_sec: float = 5.0
    backoff_factor: float = 2.0
    jitter: bool = False

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay in seconds for a given attempt (1-based index).
        Attempt 1: delay = initial_backoff_sec * (backoff_factor ** 0)
        Attempt 2: delay = initial_backoff_sec * (backoff_factor ** 1)
        """
        if attempt <= 1:
            return self.initial_backoff_sec
        return self.initial_backoff_sec * (self.backoff_factor ** (attempt - 1))


@dataclass
class JobConfig:
    """Schedule specification for an ingestion job."""
    job_id: str
    name: str
    description: str
    trigger_type: str  # 'cron' or 'interval'
    trigger_args: Dict[str, Any]
    timezone: str = "UTC"
    retry: RetryConfig = field(default_factory=RetryConfig)
    dataset_name: str = ""  # Used for DBWriter freshness tracking
    max_instances: int = 1
    coalesce: bool = True
    misfire_grace_time: int = 3600  # 1 hour grace time

    def to_summary(self) -> Dict[str, Any]:
        """Return human-readable summary of schedule."""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type,
            "trigger_args": self.trigger_args,
            "timezone": self.timezone,
            "max_attempts": self.retry.max_attempts,
            "backoff_initial_sec": self.retry.initial_backoff_sec,
            "dataset_name": self.dataset_name,
        }


class CronConfig:
    """Global configuration for automated pipeline scheduler."""

    # Explicit Timezone
    DEFAULT_TIMEZONE = "UTC"

    # Default Retry Settings
    DEFAULT_MAX_ATTEMPTS = int(os.getenv("PIPELINE_MAX_RETRIES", "3"))
    DEFAULT_INITIAL_BACKOFF = float(os.getenv("PIPELINE_BACKOFF_BASE_SEC", "5.0"))
    DEFAULT_BACKOFF_FACTOR = 2.0

    @classmethod
    def get_default_retry(cls) -> RetryConfig:
        return RetryConfig(
            max_attempts=cls.DEFAULT_MAX_ATTEMPTS,
            initial_backoff_sec=cls.DEFAULT_INITIAL_BACKOFF,
            backoff_factor=cls.DEFAULT_BACKOFF_FACTOR,
        )


# ============================================================================
# Exact PRD Schedule Definitions
# ============================================================================
# 1. Copernicus: every 6 hours
# 2. NASA GEE: daily at 02:00 UTC
# 3. NOAA: every 3 hours
# 4. INCOIS: every 12 hours
# 5. IMD: every 6 hours
# ============================================================================

JOB_SCHEDULES: Dict[str, JobConfig] = {
    "copernicus": JobConfig(
        job_id="copernicus_ingestor",
        name="Copernicus Marine Ingestion",
        description="Ingests daily SST, Chlorophyll-a, and Ocean Currents from CMEMS (every 6 hours)",
        trigger_type="cron",
        trigger_args={"hour": "*/6", "minute": "0"},
        timezone="UTC",
        retry=CronConfig.get_default_retry(),
        dataset_name="copernicus_marine",
        max_instances=1,
    ),
    "nasa_gee": JobConfig(
        job_id="nasa_gee_ingestor",
        name="NASA GEE MODIS Ingestion",
        description="Ingests daily MODIS-Aqua SST and Chlorophyll rasters (daily at 02:00 UTC)",
        trigger_type="cron",
        trigger_args={"hour": "2", "minute": "0"},
        timezone="UTC",
        retry=CronConfig.get_default_retry(),
        dataset_name="nasa_gee_modis",
        max_instances=1,
    ),
    "noaa": JobConfig(
        job_id="noaa_ingestor",
        name="NOAA Tides & Marine Weather Ingestion",
        description="Ingests CO-OPS tide observations and GFS marine wave forecasts (every 3 hours)",
        trigger_type="cron",
        trigger_args={"hour": "*/3", "minute": "0"},
        timezone="UTC",
        retry=CronConfig.get_default_retry(),
        dataset_name="noaa_weather_tides",
        max_instances=1,
    ),
    "incois": JobConfig(
        job_id="incois_scraper",
        name="INCOIS Advisory Scraper",
        description="Scrapes PFZ advisories and Ocean State Forecast (OSF) alerts (every 12 hours)",
        trigger_type="cron",
        trigger_args={"hour": "*/12", "minute": "0"},
        timezone="UTC",
        retry=CronConfig.get_default_retry(),
        dataset_name="incois_advisories",
        max_instances=1,
    ),
    "imd": JobConfig(
        job_id="imd_scraper",
        name="IMD Marine Warnings Scraper",
        description="Scrapes RSMCND cyclone / storm / coastal bulletins and CAP RSS feeds (every 6 hours)",
        trigger_type="cron",
        trigger_args={"hour": "*/6", "minute": "0"},
        timezone="UTC",
        retry=CronConfig.get_default_retry(),
        dataset_name="imd_warnings",
        max_instances=1,
    ),
}


def get_schedule_summary() -> Dict[str, Any]:
    """Return dictionary of all configured job schedules."""
    return {k: v.to_summary() for k, v in JOB_SCHEDULES.items()}

"""
Scheduler Package for NeerMitra Data Pipeline (CHUNK_ID: R4-C09)
-----------------------------------------------------------------
Automates ingestion jobs using APScheduler with exponential backoff retries.
"""

from pipeline.schedulers.cron_config import CronConfig, JobConfig, JOB_SCHEDULES

def __getattr__(name):
    if name == "PipelineSchedulerRunner":
        from pipeline.schedulers.pipeline_runner import PipelineSchedulerRunner
        return PipelineSchedulerRunner
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ["CronConfig", "JobConfig", "JOB_SCHEDULES", "PipelineSchedulerRunner"]

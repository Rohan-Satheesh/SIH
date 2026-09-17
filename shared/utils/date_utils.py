from datetime import datetime, timezone

def get_utc_now_iso() -> str:
    """Returns current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()

def get_formatted_time_utc() -> str:
    """Returns formatted HH:MM UTC time string."""
    return datetime.now(timezone.utc).strftime("%H:%M UTC")

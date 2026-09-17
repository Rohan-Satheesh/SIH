import re

def clean_marine_query(text: str) -> str:
    """Sanitizes user input string by stripping special control characters."""
    if not text:
        return ""
    return re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text).strip()

"""
ORCA Server Configuration — Environment Variables
PRD Reference: Section 7 (Infrastructure) and Section 9 (Team Roles)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://neermitra_user:neermitra_secure_2026@127.0.0.1:5432/neermitra_spatial"
)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MARINETRAFFIC_API_KEY = os.getenv("MARINETRAFFIC_API_KEY", "")
VITE_CARTO_API_KEY = os.getenv("VITE_CARTO_API_KEY", "")

# Copernicus (for satellite data pipeline)
COPERNICUS_USER = os.getenv("COPERNICUS_USER", "")
COPERNICUS_PASSWORD = os.getenv("COPERNICUS_PASSWORD", "")

# Backblaze B2 (object storage for raster data)
B2_KEY_ID = os.getenv("B2_KEY_ID", "")
B2_APP_KEY = os.getenv("B2_APP_KEY", "")
B2_BUCKET_NAME = os.getenv("B2_BUCKET_NAME", "orca-marine-data")

# Server
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Rate Limiting
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))

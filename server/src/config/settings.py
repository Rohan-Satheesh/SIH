import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://neermitra_user:neermitra_secure_2026@127.0.0.1:5432/neermitra_spatial"
)
MARINETRAFFIC_API_KEY = os.getenv("MARINETRAFFIC_API_KEY", "")
PORT = int(os.getenv("PORT", 8000))

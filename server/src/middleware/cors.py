import os

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://sih-iota-gold.vercel.app",
]

# Vercel assigns a new randomized preview URL on every non-production
# deployment (e.g. https://sih-<hash>-<team>.vercel.app). Matching that
# pattern via regex means a new preview deploy never silently breaks CORS
# the way a single hardcoded preview URL did before.
DEFAULT_ORIGIN_REGEX = r"https://sih(-[a-z0-9]+)*\.vercel\.app"


def setup_cors_middleware(app: FastAPI):
    configured_origins = os.getenv("CORS_ORIGINS", "")
    allow_origins = [
        origin.strip()
        for origin in configured_origins.split(",")
        if origin.strip()
    ] or DEFAULT_ORIGINS

    allow_origin_regex = os.getenv("CORS_ORIGIN_REGEX", DEFAULT_ORIGIN_REGEX)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_origin_regex=allow_origin_regex or None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

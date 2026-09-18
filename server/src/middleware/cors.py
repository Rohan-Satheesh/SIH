import os

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

def setup_cors_middleware(app: FastAPI):
    configured_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,"
        "https://sih-1g3odr9j8-orca-eea7.vercel.app",
    )
    allow_origins = [
        origin.strip()
        for origin in configured_origins.split(",")
        if origin.strip()
    ] or [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://sih-1g3odr9j8-orca-eea7.vercel.app",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

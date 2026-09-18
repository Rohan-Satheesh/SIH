import os

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

def setup_cors_middleware(app: FastAPI):
    configured_origins = os.getenv("CORS_ORIGINS", "*")
    allow_origins = [
        origin.strip()
        for origin in configured_origins.split(",")
        if origin.strip()
    ] or ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

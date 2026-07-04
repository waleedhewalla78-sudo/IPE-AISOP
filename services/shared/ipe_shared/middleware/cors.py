"""Hardened CORS defaults for IPE FastAPI services."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

DEFAULT_CORS_ORIGINS = "http://localhost:8082,http://localhost:3000"
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
CORS_ALLOW_HEADERS = [
    "Authorization",
    "Content-Type",
    "X-Tenant-ID",
    "X-Request-ID",
]
CORS_MAX_AGE = 3600


def parse_cors_origins(value: str | None = None) -> list[str]:
    raw = value if value is not None else os.getenv("IPE_CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def setup_cors(app: FastAPI, *, origins: list[str] | str | None = None) -> None:
    if isinstance(origins, str):
        allowed = parse_cors_origins(origins)
    elif origins is not None:
        allowed = [origin.strip() for origin in origins if origin.strip()]
    else:
        allowed = parse_cors_origins()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed,
        allow_credentials=True,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
        max_age=CORS_MAX_AGE,
    )

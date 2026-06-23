FROM python:3.12-slim AS base
LABEL build_date="2026-06-20" build_sha="current"
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml /app/pyproject.toml
COPY services/shared /app/services/shared
COPY services/network-svc/pyproject.toml /app/services/network-svc/

RUN uv sync --no-dev --directory /app/services/network-svc

COPY services/network-svc/app /app/services/network-svc/app

WORKDIR /app/services/network-svc
EXPOSE 8015
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8015"]
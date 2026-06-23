FROM python:3.12-slim AS base
LABEL build_date="2026-06-20" build_sha="current"
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml /app/pyproject.toml
COPY services/shared /app/services/shared
COPY services/quality-svc/pyproject.toml /app/services/quality-svc/

RUN uv sync --no-dev --directory /app/services/quality-svc

COPY services/quality-svc/app /app/services/quality-svc/app

WORKDIR /app/services/quality-svc
EXPOSE 8013
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8013"]
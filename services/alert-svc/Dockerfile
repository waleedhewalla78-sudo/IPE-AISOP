FROM python:3.12-slim AS base
LABEL build_date="2026-06-17" build_sha="current"
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml /app/pyproject.toml
COPY services/shared /app/services/shared
COPY services/alert-svc/pyproject.toml /app/services/alert-svc/

RUN uv sync --no-dev --directory /app/services/alert-svc

COPY services/alert-svc/app /app/services/alert-svc/app

WORKDIR /app/services/alert-svc
EXPOSE 8010
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]

FROM python:3.12-slim AS base
LABEL build_date="2026-06-17" build_sha="current"
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml /app/pyproject.toml
COPY services/shared /app/services/shared
COPY services/fea-svc/pyproject.toml /app/services/fea-svc/

RUN uv sync --no-dev --directory /app/services/fea-svc

COPY services/fea-svc/app /app/services/fea-svc/app

WORKDIR /app/services/fea-svc
EXPOSE 8004
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]


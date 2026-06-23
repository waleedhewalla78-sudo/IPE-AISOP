FROM python:3.12-slim AS base
LABEL build_date="2026-06-17" build_sha="current"
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml /app/pyproject.toml
COPY services/shared /app/services/shared
COPY services/nlp-svc/pyproject.toml /app/services/nlp-svc/

RUN uv sync --no-dev --directory /app/services/nlp-svc

COPY services/nlp-svc/app /app/services/nlp-svc/app

WORKDIR /app/services/nlp-svc
EXPOSE 8007
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]


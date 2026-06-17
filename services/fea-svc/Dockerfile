FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# Copy pyproject and lock for the service
COPY services/fea-svc/pyproject.toml services/fea-svc/uv.lock ./
# Copy shared package
COPY services/shared ./shared

# Install dependencies (including shared) and make them available system-wide
RUN uv sync --no-dev && cp -r .venv/lib/python3.12/site-packages/* /usr/local/lib/python3.12/site-packages/

# Copy service source code
COPY services/fea-svc/app ./app

EXPOSE 8004
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]

FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml /app/pyproject.toml
COPY services/shared /app/services/shared
COPY services/material-svc/pyproject.toml /app/services/material-svc/
RUN uv sync --no-dev --directory /app/services/material-svc
COPY services/material-svc/app /app/services/material-svc/app
WORKDIR /app/services/material-svc
EXPOSE 8090
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090"]

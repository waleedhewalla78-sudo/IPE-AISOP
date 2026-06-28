FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml /app/pyproject.toml
COPY services/shared /app/services/shared
COPY services/scenario-svc/pyproject.toml /app/services/scenario-svc/
RUN uv sync --no-dev --directory /app/services/scenario-svc
COPY services/scenario-svc/app /app/services/scenario-svc/app
WORKDIR /app/services/scenario-svc
EXPOSE 8050
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8050"]

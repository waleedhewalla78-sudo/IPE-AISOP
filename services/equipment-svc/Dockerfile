FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml /app/pyproject.toml
COPY services/shared /app/services/shared
COPY services/equipment-svc/pyproject.toml /app/services/equipment-svc/
RUN uv sync --no-dev --directory /app/services/equipment-svc
COPY services/equipment-svc/app /app/services/equipment-svc/app
WORKDIR /app/services/equipment-svc
EXPOSE 8061
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8061"]

FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml /app/pyproject.toml
COPY services/shared /app/services/shared
COPY services/demand-svc/pyproject.toml /app/services/demand-svc/
RUN uv sync --no-dev --directory /app/services/demand-svc
COPY services/demand-svc/app /app/services/demand-svc/app
WORKDIR /app/services/demand-svc
EXPOSE 8040
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8040"]

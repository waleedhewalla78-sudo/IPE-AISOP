FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml /app/pyproject.toml
COPY services/shared /app/services/shared
COPY services/upload-svc/pyproject.toml /app/services/upload-svc/
RUN uv sync --no-dev --directory /app/services/upload-svc
COPY services/upload-svc/app /app/services/upload-svc/app
WORKDIR /app/services/upload-svc
EXPOSE 8120
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8120"]

FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml /app/pyproject.toml
COPY services/shared /app/services/shared
COPY services/sop-svc/pyproject.toml /app/services/sop-svc/
RUN uv sync --no-dev --directory /app/services/sop-svc
COPY services/sop-svc/app /app/services/sop-svc/app
WORKDIR /app/services/sop-svc
EXPOSE 8110
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8110"]

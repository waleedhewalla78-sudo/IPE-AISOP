FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml /app/pyproject.toml
COPY services/shared /app/services/shared
COPY services/procurement-svc/pyproject.toml /app/services/procurement-svc/
RUN uv sync --no-dev --directory /app/services/procurement-svc
COPY services/procurement-svc/app /app/services/procurement-svc/app
WORKDIR /app/services/procurement-svc
EXPOSE 8100
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]

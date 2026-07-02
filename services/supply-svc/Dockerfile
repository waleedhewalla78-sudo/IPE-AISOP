FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml /app/pyproject.toml
COPY services/shared /app/services/shared
COPY services/supply-svc/pyproject.toml /app/services/supply-svc/
RUN uv sync --no-dev --directory /app/services/supply-svc
COPY services/supply-svc/app /app/services/supply-svc/app
WORKDIR /app/services/supply-svc
EXPOSE 8060
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8060"]

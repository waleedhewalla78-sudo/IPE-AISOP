FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml /app/pyproject.toml
COPY services/shared /app/services/shared
COPY services/order-svc/pyproject.toml /app/services/order-svc/
RUN uv sync --no-dev --directory /app/services/order-svc
COPY services/order-svc/app /app/services/order-svc/app
WORKDIR /app/services/order-svc
EXPOSE 8070
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8070"]

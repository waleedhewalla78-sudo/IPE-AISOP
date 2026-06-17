FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY services/res-svc/pyproject.toml services/res-svc/uv.lock ./
COPY services/shared ./shared
RUN uv sync --no-dev && cp -r .venv/lib/python3.12/site-packages/* /usr/local/lib/python3.12/site-packages/
COPY services/res-svc/pyproject.toml services/res-svc/uv.lock ./
RUN uv sync --no-dev
COPY services/res-svc/app ./app
EXPOSE 8005
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]

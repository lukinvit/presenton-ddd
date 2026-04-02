FROM python:3.12-slim AS base

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy workspace root (needed for uv workspace resolution)
COPY pyproject.toml uv.lock ./
COPY shared/ ./shared/
COPY gateway/ ./gateway/

# Install gateway + shared in the workspace context
RUN uv sync --package presenton-gateway --no-dev

FROM base AS runtime

WORKDIR /app/gateway

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose FastAPI gateway port
EXPOSE 8000

CMD ["uv", "run", "--package", "presenton-gateway", \
     "uvicorn", "api_gateway.app:app", "--host", "0.0.0.0", "--port", "8000"]

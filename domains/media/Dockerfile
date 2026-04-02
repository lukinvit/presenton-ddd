FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
COPY shared/ ./shared/
COPY domains/media/ ./domains/media/

RUN uv sync --frozen --package presenton-media --no-dev

# ── Runtime ───────────────────────────────────────────────────────────────────

FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/domains/media /app/domains/media

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8050 9050

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8050"]

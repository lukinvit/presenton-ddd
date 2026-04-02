FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
COPY shared/ ./shared/
COPY domains/auth/ ./domains/auth/

RUN uv sync --frozen --package presenton-auth --no-dev

# ── Runtime ───────────────────────────────────────────────────────────────────

FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/domains/auth /app/domains/auth

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8070 9070

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8070"]

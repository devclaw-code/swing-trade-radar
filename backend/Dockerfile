# syntax=docker/dockerfile:1.7
# ---------- Stage 1: builder ----------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Build deps for any wheels that need compiling (numpy/pandas usually have wheels, but keep gcc just in case)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Resolve + install deps first for layer caching
COPY pyproject.toml uv.lock ./
# Copy package source before sync because the project is a package (uv build needs it)
COPY src/ ./src/
RUN uv sync --frozen --no-dev

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Minimal runtime libs (libgomp1 for numpy/pandas BLAS)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app --no-create-home app

# Copy venv + source from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src/swing_trader /app/swing_trader

# Writable data dir for SQLite
RUN mkdir -p /app/var && chown -R app:app /app

VOLUME ["/app/var"]
EXPOSE 8000
USER app

CMD ["python", "-m", "swing_trader.main"]

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install uv
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && ln -s /root/.local/bin/uv /usr/local/bin/uv

# Copy source code first (needed for package installation)
COPY src ./src

# Copy project metadata and lockfile, install dependencies (no dev)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Defaults (overridable at runtime)
ENV DATA_DIR=/data \
    CONFIG_DIR=/data/config \
    TZ=UTC

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Entrypoint: run the package main (using the project's virtualenv)
CMD ["python", "-m", "telegram_antilurk_bot"]


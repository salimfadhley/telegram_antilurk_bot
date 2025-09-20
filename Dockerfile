FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install uv
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh -s -- -y \
    && ln -s /root/.local/bin/uv /usr/local/bin/uv

# Copy project metadata and lockfile, install dependencies (no dev)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy source code
COPY src ./src

# Defaults (overridable at runtime)
ENV DATA_DIR=/data \
    CONFIG_DIR=/data/config \
    TZ=UTC

# Entrypoint: run the package main (using the project's virtualenv)
CMD ["python", "-m", "telegram_antilurk_bot"]


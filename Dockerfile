FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS builder

# Enable bytecode compilation for faster startup performance
ENV UV_COMPILE_BYTECODE=1

WORKDIR /uv-build

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

FROM python:3.10-slim-bookworm

# Install wget for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ticket-platform

COPY --from=builder /uv-build/.venv /ticket-platform/.venv

ENV PATH="/ticket-platform/.venv/bin:$PATH"

COPY ./app /ticket-platform/app

# Copy the migration setup and alembic.ini
COPY ./migrations /ticket-platform/migrations
COPY ./alembic.ini /ticket-platform/alembic.ini

# Copy SQLite directory and file
COPY ./db /ticket-platform/db

# Update alembic.ini script_location with the appropriate path
RUN sed -i 's/^\s*script_location\s*=\s*.*/script_location = \/ticket-platform\/migrations/' /ticket-platform/alembic.ini

COPY ./config/entrypoint.sh /entrypoint

ENTRYPOINT ["/entrypoint"]

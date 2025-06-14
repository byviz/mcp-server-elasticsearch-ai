# Multi-stage Dockerfile for Datadog MCP Server
ARG PYTHON_VERSION=3.12
ARG BUILD_ENV=production

# Base image with security updates
FROM python:${PYTHON_VERSION}-slim AS base
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Builder stage
FROM base AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Create directory with proper permissions
RUN mkdir -p /app/.uv && chmod -R 777 /app

# Copy dependency files first (better caching)
COPY pyproject.toml ./

# Install dependencies based on build environment
RUN if [ "$BUILD_ENV" = "ci" ]; then \
        uv sync --no-install-project --dev; \
    else \
        uv sync --no-install-project; \
    fi

# Copy source code
COPY . .

# Install the application
RUN uv pip install --no-deps .

# Production stage
FROM base AS production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --shell /bin/bash --create-home app

# Install uv in production
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Create proper directory structure with appropriate permissions
RUN mkdir -p /app/.uv && \
    chmod -R 777 /app

# Copy virtual environment and app from builder
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/datadog_mcp /app/datadog_mcp

# Copy tests and config files for CI builds
COPY --from=builder --chown=app:app /app/tests /app/tests
COPY --from=builder --chown=app:app /app/pyproject.toml /app/pyproject.toml
COPY --from=builder --chown=app:app /app/README.md /app/README.md

# Fix permissions on copied files
RUN chmod -R 777 /app/.venv && \
    chmod -R 777 /app/datadog_mcp && \
    chmod -R 777 /app/tests || true

# Set up PATH for virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Switch to non-root user
USER app

# Set Python environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set entrypoint to uv run
ENTRYPOINT ["uv", "run"]

# Default command to start MCP server
CMD ["python", "-m", "datadog_mcp"]

# Metadata labels
LABEL org.opencontainers.image.title="Datadog MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for Datadog integration"
LABEL org.opencontainers.image.vendor="Datadog MCP Project"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/brukhabtu/datadog-mcp"
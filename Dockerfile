# ============================================
# Dagster Application Dockerfile (Multi-Stage Build)
# ============================================
# Stage 1: Builder - Install dependencies with uv
# Stage 2: Development - Full development environment
# Stage 3: Production - Minimal production image (webserver)
# Stage 4: Daemon - Background scheduler service
# ============================================

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package installer)
RUN pip install --no-cache-dir uv

# Copy dependency files first (layer caching optimization)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using uv
# --frozen ensures reproducible builds from uv.lock
RUN uv sync --frozen

# ============================================
# Stage 2: Development
# ============================================
FROM python:3.12-slim AS development

# Set working directory
WORKDIR /app

# Install system dependencies for runtime (curl for healthcheck)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv in runtime stage (needed for uv run command)
RUN pip install --no-cache-dir uv

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy installed dependencies from builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy Dagster instance and workspace configuration (changes less frequently)
COPY --chown=appuser:appuser dagster.yaml /app/.dagster/dagster.yaml
COPY --chown=appuser:appuser workspace.yaml /app/workspace.yaml

# Copy application code (in development, this gets overridden by volume mount)
COPY --chown=appuser:appuser dagster_project ./dagster_project

# Create necessary directories
RUN mkdir -p /app/.dagster /app/artifacts && \
    chown -R appuser:appuser /app/.dagster /app/artifacts

# Switch to non-root user
USER appuser

# Environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DAGSTER_HOME=/app/.dagster

# Expose Dagster web UI port
EXPOSE 3000

# Default command for development - runs Dagster dev server
CMD ["uv", "run", "dagster", "dev", "--host", "0.0.0.0", "--port", "3000"]

# ============================================
# Stage 3: Production (Webserver)
# ============================================
FROM python:3.12-slim AS production

# Set working directory
WORKDIR /app

# Install system dependencies for runtime (curl for healthcheck)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv in runtime stage (needed for uv run command)
RUN pip install --no-cache-dir uv

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy installed dependencies from builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy Dagster instance and workspace configuration (changes less frequently)
COPY --chown=appuser:appuser dagster.yaml /app/.dagster/dagster.yaml
COPY --chown=appuser:appuser workspace.yaml /app/workspace.yaml

# Copy metadata files
COPY --chown=appuser:appuser pyproject.toml README.md ./

# Copy application code (changes most frequently)
COPY --chown=appuser:appuser dagster_project ./dagster_project

# Create necessary directories
RUN mkdir -p /app/.dagster /app/artifacts && \
    chown -R appuser:appuser /app/.dagster /app/artifacts

# Switch to non-root user
USER appuser

# Environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DAGSTER_HOME=/app/.dagster

# Expose Dagster web UI port
EXPOSE 3000

# Default command for production - runs Dagster webserver only (daemon runs separately)
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]

# ============================================
# Stage 4: Daemon (Background Scheduler)
# ============================================
FROM production AS daemon

# Run Dagster daemon instead of webserver
CMD ["dagster-daemon", "run"]

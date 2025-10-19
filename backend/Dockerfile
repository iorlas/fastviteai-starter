# Build stage: Install dependencies with uv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install dependencies first (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --locked --no-install-project --no-dev

# Copy application code and install project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked --no-dev


# Runtime stage: Lightweight final image
FROM python:3.12-slim-bookworm AS runtime

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
  && useradd --system --gid 999 --uid 999 --create-home nonroot

# Install system dependencies for faster-whisper and audio processing
# libgomp1: GNU OpenMP library (required by faster-whisper)
# ffmpeg: Audio/video processing (required for WebM decoding)
RUN apt-get update && apt-get install -y --no-install-recommends \
  libgomp1 \
  ffmpeg \
  && rm -rf /var/lib/apt/lists/*

# Create cache directory with proper ownership BEFORE switching users
# This ensures the volume mount point has correct permissions
RUN mkdir -p /home/nonroot/.cache && \
  chown -R nonroot:nonroot /home/nonroot/.cache

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH" \
  PYTHONUNBUFFERED=1 \
  HOME="/home/nonroot" \
  HF_HOME="/home/nonroot/.cache/huggingface" \
  TORCH_HOME="/home/nonroot/.cache/torch"

# Copy the application from the builder
COPY --from=builder --chown=nonroot:nonroot /app /app

# Use the non-root user to run our application
USER nonroot

# Use `/app` as the working directory
WORKDIR /app

# Expose FastAPI port
EXPOSE 8000

# Health check (optional but recommended)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"

# Run uvicorn with hot reload for development
# Production: Remove --reload flag
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

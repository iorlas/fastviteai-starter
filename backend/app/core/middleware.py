"""Middleware components for request processing.

This module provides middleware for:
- Request ID generation and propagation
- Structured logging configuration with request context
"""

import logging
import time
import uuid
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.settings import Environment, settings

# Configure structlog based on environment
# Development: Colorful console output for easy reading
# Production: JSON structured logging for parsing
if settings.environment == Environment.PRODUCTION:
    renderer = structlog.processors.JSONRenderer()
else:
    renderer = structlog.dev.ConsoleRenderer(colors=True)

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        renderer,
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that generates a unique request ID for each incoming request.

    The request ID is:
    1. Generated as a UUID4
    2. Added to the structlog context for automatic inclusion in all logs
    3. Included in the response headers as 'X-Request-ID'

    Logging behavior varies by environment:
    - Development: Single compact log on completion (e.g., "GET /api/v1/health → 200")
    - Production: Separate logs for request start and completion with full details

    This enables request tracing across the application and correlating logs
    for a specific request.

    Usage:
        app.add_middleware(RequestIDMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and inject request ID into logs and response."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add request ID to structlog context for all subsequent log calls
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        logger = structlog.get_logger()

        # Track request duration
        start_time = time.perf_counter()

        # Production: Log both start and completion with full details
        if settings.environment == Environment.PRODUCTION:
            logger.info(
                "request_started",
                method=request.method,
                path=request.url.path,
                query_params=str(request.url.query) if request.url.query else None,
                client=request.client.host if request.client else None,
            )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Log request completion
        if settings.environment == Environment.PRODUCTION:
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
        else:
            # Development: Compact one-line log with shortened request ID
            short_id = request_id[-8:]
            path_with_query = str(request.url.path)
            if request.url.query:
                path_with_query = f"{request.url.path}?{request.url.query}"
            logger.info(
                f"{request.method} {path_with_query}",
                code=response.status_code,
                t=round(duration_ms, 2),
                request_id=short_id,
            )

        return response

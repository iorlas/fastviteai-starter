"""Health check endpoints for monitoring application and database status.

This module provides:
- Basic liveness check (/health)
- Database connectivity check (/health/db)

These endpoints are used by:
- Container orchestration (Docker, Kubernetes) for health probes
- Load balancers for routing decisions
- Monitoring systems for alerting
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from .schemas import DatabaseHealthResponse, HealthResponse
from .service import HealthService

router = APIRouter(prefix="/api/v1", tags=["health"])


def get_health_service(db: Annotated[AsyncSession, Depends(get_db)]) -> HealthService:
    """Dependency injection for HealthService."""
    return HealthService(db)


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(
    service: Annotated[HealthService, Depends(get_health_service)],
) -> HealthResponse:
    """Basic health check endpoint for liveness probes.

    This endpoint verifies that the application is running and responsive.
    It does not check external dependencies like database.

    Args:
        service: HealthService injected via dependency

    Returns:
        HealthResponse: Status indicating the application is running

    Example response:
        {"status": "healthy"}
    """
    return await service.check_basic_health()


@router.get("/health/db")
async def health_check_db(
    response: Response,
    service: Annotated[HealthService, Depends(get_health_service)],
) -> DatabaseHealthResponse:
    """Database connectivity health check for readiness probes.

    Attempts to execute a simple query to verify database connection.
    Returns 200 if database is reachable, 503 if connection fails.

    This endpoint is used by readiness probes to determine if the
    application can serve traffic.

    Args:
        response: FastAPI response object for setting status code
        service: HealthService injected via dependency

    Returns:
        DatabaseHealthResponse: Status indicating database connectivity

    Example response (healthy):
        {"status": "healthy", "database": "connected"}

    Example response (unhealthy):
        {"status": "unhealthy", "database": "disconnected", "error": "connection refused"}
    """
    result = await service.check_database_health()

    # Set appropriate HTTP status code based on health
    if result.status == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        response.status_code = status.HTTP_200_OK

    return result

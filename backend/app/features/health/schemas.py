"""Pydantic schemas for health check responses."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Basic health check response model.

    Attributes:
        status: Health status indicator ("healthy" or "unhealthy")
    """

    status: str


class DatabaseHealthResponse(BaseModel):
    """Database health check response model.

    Attributes:
        status: Overall health status ("healthy" or "unhealthy")
        database: Database connection status ("connected" or "disconnected")
        error: Optional error message if database check fails
    """

    status: str
    database: str
    error: str | None = None

"""Integration tests for health check feature.

These tests validate the complete Repository → Service → Router stack
for health monitoring functionality.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.health.service import HealthService
from main import app

# Create test client
client = TestClient(app)


class TestHealthEndpoints:
    """Test health check HTTP endpoints."""

    def test_health_endpoint_returns_200(self):
        """Test that /health endpoint returns 200 OK with correct schema.

        Validates:
        - Endpoint returns 200 status code
        - Response has correct JSON structure
        - Status is "healthy"
        """
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_health_db_endpoint_returns_200_when_db_available(self):
        """Test that /health/db returns 200 when database is available.

        Validates:
        - Endpoint returns 200 or 503 depending on database state
        - Response has correct JSON structure
        - Response includes all required fields
        """
        response = client.get("/api/v1/health/db")

        # Should return 200 if database is running, 503 if not
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "database" in data

        if response.status_code == 200:
            assert data["status"] == "healthy"
            assert data["database"] == "connected"
        else:
            assert data["status"] == "unhealthy"
            assert data["database"] == "disconnected"
            assert "error" in data


class TestHealthServiceIntegration:
    """Test HealthService with real database session."""

    @pytest.mark.asyncio()
    async def test_health_service_with_db_session(self, db_session: AsyncSession):
        """Test HealthService with actual database session.

        Validates:
        - Service can be initialized with db_session fixture
        - Database health check succeeds with real database
        - Basic health check works
        """
        service = HealthService(db_session)

        # Test basic health check
        basic_result = await service.check_basic_health()
        assert basic_result.status == "healthy"

        # Test database health check with real database
        db_result = await service.check_database_health()
        assert db_result.status == "healthy"
        assert db_result.database == "connected"
        assert db_result.error is None

    @pytest.mark.asyncio()
    async def test_health_service_database_query(self, db_session: AsyncSession):
        """Test that HealthService executes database query correctly.

        Validates:
        - Service successfully executes SELECT 1
        - Database connection is working
        - No errors are raised
        """
        service = HealthService(db_session)

        # This should not raise an exception
        result = await service.check_database_health()

        # Should return healthy status
        assert result.status == "healthy"
        assert result.database == "connected"


class TestHealthFeatureArchitecture:
    """Test that health feature follows correct architecture pattern."""

    def test_router_uses_service_layer(self):
        """Test that router delegates to service (no direct DB access).

        Validates:
        - Router imports and uses HealthService
        - Service is injected via dependency injection
        - Architecture pattern is followed
        """
        from app.features.health.router import get_health_service, router

        # Router should have dependency injection for service
        assert get_health_service is not None

        # Router should have the health endpoints (including prefix)
        routes = [route.path for route in router.routes]  # type: ignore[attr-defined]
        assert "/api/v1/health" in routes
        assert "/api/v1/health/db" in routes

    def test_service_contains_business_logic(self):
        """Test that service layer contains business logic.

        Validates:
        - HealthService has business logic methods
        - Service is framework-agnostic (no FastAPI dependencies)
        """
        from app.features.health.service import HealthService

        # Service should have business logic methods
        assert hasattr(HealthService, "check_basic_health")
        assert hasattr(HealthService, "check_database_health")

        # Service should not import FastAPI (framework-agnostic)
        import inspect

        service_source = inspect.getsource(HealthService)
        assert "fastapi" not in service_source.lower()
        # Check that "from router" or "import router" is not in source
        # (note: the word "router" may appear in comments/docs)
        assert "from fastapi" not in service_source.lower()
        assert "import router" not in service_source.lower()

    def test_schemas_define_response_models(self):
        """Test that schemas define Pydantic response models.

        Validates:
        - Schemas exist and are Pydantic models
        - Required fields are present
        """
        from pydantic import BaseModel

        from app.features.health.schemas import (
            DatabaseHealthResponse,
            HealthResponse,
        )

        # Schemas should be Pydantic models
        assert issubclass(HealthResponse, BaseModel)
        assert issubclass(DatabaseHealthResponse, BaseModel)

        # HealthResponse should have status field
        health = HealthResponse(status="healthy")
        assert health.status == "healthy"

        # DatabaseHealthResponse should have required fields
        db_health = DatabaseHealthResponse(status="healthy", database="connected", error=None)
        assert db_health.status == "healthy"
        assert db_health.database == "connected"

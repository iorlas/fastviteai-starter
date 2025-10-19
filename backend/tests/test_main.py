"""Integration tests for FastAPI application.

Tests cover:
- Health check endpoints
- CORS middleware
- Request ID middleware
- Custom exception handlers
- OpenAPI specification availability
"""

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from main import app

# Create test client
client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_endpoint_returns_200(self):
        """Test that /health endpoint returns 200 OK."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_health_db_endpoint_returns_200_when_db_available(self):
        """Test that /health/db returns 200 when database is available."""
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


class TestCORSMiddleware:
    """Test CORS middleware configuration."""

    def test_cors_headers_present_in_response(self):
        """Test that CORS headers are present in responses."""
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers

    def test_cors_preflight_request(self):
        """Test CORS preflight OPTIONS request."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        # Should return 200 for preflight
        assert response.status_code == 200


class TestRequestIDMiddleware:
    """Test Request ID middleware functionality."""

    def test_request_id_present_in_response_headers(self):
        """Test that X-Request-ID header is added to responses."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "x-request-id" in response.headers
        # Request ID should be a valid UUID format
        request_id = response.headers["x-request-id"]
        assert len(request_id) == 36  # UUID4 format with hyphens
        assert request_id.count("-") == 4

    def test_different_requests_have_different_request_ids(self):
        """Test that each request gets a unique request ID."""
        response1 = client.get("/api/v1/health")
        response2 = client.get("/api/v1/health")

        request_id1 = response1.headers["x-request-id"]
        request_id2 = response2.headers["x-request-id"]

        assert request_id1 != request_id2


class TestExceptionHandlers:
    """Test custom exception handlers."""

    def test_not_found_error_returns_404(self):
        """Test that NotFoundError returns 404 with correct JSON format."""

        # Create a test endpoint that raises NotFoundError
        @app.get("/test/not-found")
        async def test_not_found():
            raise NotFoundError("Resource not found")

        response = client.get("/test/not-found")
        assert response.status_code == 404
        assert response.json() == {"detail": "Resource not found"}

    def test_forbidden_error_returns_403(self):
        """Test that ForbiddenError returns 403 with correct JSON format."""

        # Create a test endpoint that raises ForbiddenError
        @app.get("/test/forbidden")
        async def test_forbidden():
            raise ForbiddenError("Access denied")

        response = client.get("/test/forbidden")
        assert response.status_code == 403
        assert response.json() == {"detail": "Access denied"}

    def test_validation_error_returns_422(self):
        """Test that ValidationError returns 422 with correct JSON format."""

        # Create a test endpoint that raises ValidationError
        @app.get("/test/validation")
        async def test_validation():
            raise ValidationError("Invalid input")

        response = client.get("/test/validation")
        assert response.status_code == 422
        assert response.json() == {"detail": "Invalid input"}


class TestOpenAPISpec:
    """Test OpenAPI specification availability."""

    def test_openapi_spec_accessible(self):
        """Test that OpenAPI spec is accessible at default FastAPI path."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        spec = response.json()
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec
        # Verify our health endpoints are in the spec (with full prefix)
        assert "/api/v1/health" in spec["paths"]
        assert "/api/v1/health/db" in spec["paths"]

    def test_openapi_docs_accessible(self):
        """Test that Swagger UI docs are accessible at default FastAPI path."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""FastAPI application initialization and configuration.

This module creates and configures the main FastAPI application with:
- CORS middleware for frontend integration
- Request ID middleware for request tracing
- Custom exception handlers for domain errors
- API versioning with /api/v1 prefix
- Health check endpoints
- OpenAPI documentation
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.middleware import RequestIDMiddleware
from app.core.settings import settings
from app.features.health.router import router as health_router
from app.features.todos.router import router as todos_router

# Create FastAPI application
app = FastAPI(
    title="Boilerplate API",
    version="1.0.0",
    description="A modern full-stack boilerplate with FastAPI backend and React frontend",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Add Request ID middleware
app.add_middleware(RequestIDMiddleware)


# Exception handlers
@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle NotFoundError exceptions and return 404 responses."""
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


@app.exception_handler(ForbiddenError)
async def forbidden_exception_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
    """Handle ForbiddenError exceptions and return 403 responses."""
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc)},
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle ValidationError exceptions and return 422 responses."""
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )


# Include API routers
app.include_router(health_router)
app.include_router(todos_router)

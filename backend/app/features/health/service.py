"""Health check service containing business logic for health monitoring.

This service handles:
- Basic application liveness checks
- Database connectivity validation
- Error handling and status determination
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import DatabaseHealthResponse, HealthResponse


class HealthService:
    """Service for health check operations.

    This service provides health monitoring functionality following the
    Repository → Service → Router pattern. Business logic is encapsulated
    here to keep routers thin and testable.

    Design Decision: Direct DB Access
        This service takes AsyncSession directly instead of using a repository
        because it only performs simple diagnostic queries (SELECT 1). For such
        straightforward operations without complex data access patterns, using
        a repository would add unnecessary abstraction overhead.

        Use repositories when:
        - Performing CRUD operations on domain entities
        - Need complex queries with filtering, sorting, pagination
        - Business logic requires multiple related database operations

        Use direct DB access when:
        - Simple diagnostic/health check queries
        - One-off utility operations
        - No need for query reuse or testing isolation

    Attributes:
        db: Async database session for connectivity checks
    """

    def __init__(self, db: AsyncSession):
        """Initialize health service with database session.

        Args:
            db: Async SQLAlchemy session for database operations
        """
        self.db = db

    async def check_basic_health(self) -> HealthResponse:
        """Perform basic application liveness check.

        This check verifies that the application is running and responsive.
        It does not check external dependencies like database.

        Returns:
            HealthResponse: Status indicating application is alive

        Example:
            service = HealthService(db)
            health = await service.check_basic_health()
            assert health.status == "healthy"
        """
        return HealthResponse(status="healthy")

    async def check_database_health(self) -> DatabaseHealthResponse:
        """Perform database connectivity health check.

        Attempts to execute a simple query to verify database connection.
        This is used by readiness probes to determine if the application
        can serve traffic.

        Returns:
            DatabaseHealthResponse: Detailed database connectivity status

        Example:
            service = HealthService(db)
            health = await service.check_database_health()
            if health.status == "healthy":
                print("Database is connected")
            else:
                print(f"Database error: {health.error}")
        """
        try:
            # Execute simple query to test database connection
            await self.db.execute(text("SELECT 1"))
            return DatabaseHealthResponse(status="healthy", database="connected")
        except Exception as e:
            # Database connection failed - return unhealthy status with error
            return DatabaseHealthResponse(status="unhealthy", database="disconnected", error=str(e))

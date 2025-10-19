"""Pytest fixtures for test infrastructure.

This module provides pytest fixtures for database testing with testcontainers.
It configures:
- Session-scoped PostgreSQL container (reused across all tests)
- Function-scoped database sessions with transaction isolation
- Test client for integration tests
- pytest-xdist compatibility for parallel test execution

Fixtures:
    db_container: Session-scoped PostgreSQL 16 container
    db_session: Function-scoped database session with transaction rollback
    test_client: TestClient for FastAPI integration tests
"""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from main import app


@pytest.fixture(scope="session")
def db_container() -> Generator[PostgresContainer, None, None]:
    """Provide session-scoped PostgreSQL 16 testcontainer.

    This fixture spins up a PostgreSQL 16 container once per test session
    and reuses it across all tests. The container is automatically cleaned up
    after the test session ends.

    pytest-xdist compatibility:
    When running tests in parallel with pytest-xdist (pytest -n auto), each
    worker process gets its own container. This ensures test isolation between
    parallel workers while still reusing the container within each worker.

    Returns:
        PostgresContainer: Running PostgreSQL 16 container instance

    Example:
        def test_something(db_container):
            # Container is available and running
            assert db_container.get_container_host_ip() is not None
    """
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as container:
        # Set environment variable for Alembic to use test database
        test_db_url = container.get_connection_url().replace(
            "postgresql+psycopg://",
            "postgresql+psycopg://",
        )
        os.environ["DATABASE_URL"] = test_db_url.replace(
            "postgresql+psycopg://",
            "postgresql+asyncpg://",
        )

        # Run Alembic migrations against test container
        import subprocess

        subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
        )

        yield container


@pytest_asyncio.fixture(scope="function")
async def db_session(db_container: PostgresContainer) -> AsyncGenerator[AsyncSession, None]:
    """Provide function-scoped database session with transaction isolation.

    This fixture creates a new database session for each test function and uses
    a savepoint/rollback pattern to ensure test isolation. Changes made in one
    test do not affect other tests.

    Transaction Isolation Pattern:
    1. Begin outer transaction
    2. Create savepoint (nested transaction)
    3. Yield session to test
    4. Roll back to savepoint (discards all test changes)
    5. Close session

    This approach is faster than recreating the database or truncating tables
    between tests while providing complete isolation.

    pytest-xdist compatibility:
    Each worker process has its own container (from db_container fixture), so
    sessions from different workers are completely independent. No coordination
    or locking needed.

    Args:
        db_container: PostgreSQL container from session-scoped fixture

    Yields:
        AsyncSession: Isolated database session for the test

    Example:
        async def test_create_user(db_session):
            user = User(email="test@example.com", hashed_password="hashed")
            db_session.add(user)
            await db_session.commit()
            # User will be rolled back after test completes
    """
    # Get connection URL from container and convert to async driver
    connection_url = db_container.get_connection_url().replace(
        "postgresql+psycopg://",
        "postgresql+asyncpg://",
    )

    # Create async engine for this test
    engine = create_async_engine(connection_url, echo=False, future=True)

    # Create async session factory
    async_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # Create connection
    async with engine.connect() as connection:
        # Begin transaction
        transaction = await connection.begin()

        # Create session bound to the connection
        session = async_session_factory(bind=connection)

        # Yield session to test
        yield session

        # Rollback transaction (discards all test changes)
        await session.close()
        await transaction.rollback()

    # Dispose engine after test
    await engine.dispose()


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests.

    This fixture ensures that the event loop is properly configured for
    session-scoped async fixtures (like db_container).

    Returns:
        asyncio.AbstractEventLoop: Event loop for the test session
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def test_client(db_container: PostgresContainer) -> Generator[TestClient, None, None]:
    """Provide TestClient for FastAPI integration tests.

    This fixture creates a test client for making HTTP requests to the FastAPI
    application. The client handles the full request/response cycle including
    middleware, validation, and serialization.

    Overrides the database dependency to use the test container database,
    ensuring integration tests run against the test database.

    Uses context manager to ensure proper cleanup of async resources between tests.

    Benefits:
    - Centralized client configuration
    - Easier to modify client settings in one place
    - Better test isolation with proper cleanup
    - Uses test database instead of production database

    Args:
        db_container: PostgreSQL container for test database

    Yields:
        TestClient: Configured test client for the FastAPI app

    Example:
        def test_health_check(test_client):
            response = test_client.get("/api/v1/health")
            assert response.status_code == 200
    """
    # Import here to avoid circular imports
    from app.core.database import get_db

    # Create a new engine for the test database
    connection_url = db_container.get_connection_url().replace(
        "postgresql+psycopg://",
        "postgresql+asyncpg://",
    )

    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.orm import sessionmaker

    test_engine = create_async_engine(connection_url, echo=False, future=True)
    test_session_local = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        """Override database dependency to use test database."""
        async with test_session_local() as session:
            try:
                yield session
            finally:
                await session.close()

    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client
    finally:
        # Clean up dependency override
        app.dependency_overrides.clear()

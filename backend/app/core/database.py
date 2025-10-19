"""Database session management with SQLAlchemy.

This module provides:
- Async database engine configuration
- Session factory for dependency injection
- Base class for SQLAlchemy models
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.settings import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.log_level == "DEBUG",
    future=True,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for SQLAlchemy models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for injecting database sessions into FastAPI endpoints.

    Usage:
        from typing import Annotated

        @app.get("/users/{user_id}")
        async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalars().first()

    Yields:
        AsyncSession: Database session that automatically closes after request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

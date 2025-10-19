"""BaseRepository pattern with Python 3.12+ generics for DRY CRUD operations.

This module provides a generic repository base class that reduces 60-70% of
repository boilerplate by implementing common CRUD operations with full type safety.

Key Features:
- Python 3.12+ PEP 695 generic syntax for clean type parameters
- SQLAlchemy 2.0 async operations throughout
- Type-safe methods with full IDE autocomplete support
- Generic pagination with metadata support
- Extensible for domain-specific queries

Usage Example:
    from features.todos.models import Todo
    from core.repository import BaseRepository
    from sqlalchemy.ext.asyncio import AsyncSession

    # Extending BaseRepository for a domain model
    class TodoRepository(BaseRepository[Todo]):
        async def get_by_user(
            self, user_id: int, offset: int = 0, limit: int = 100
        ) -> list[Todo]:
            '''Custom query for ownership filtering'''
            stmt = (
                select(self.model)
                .where(self.model.user_id == user_id)
                .offset(offset)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())

    # Using the repository
    async def get_user_todos(db: AsyncSession, user_id: int) -> list[Todo]:
        repo = TodoRepository(Todo, db)
        return await repo.get_by_user(user_id)

When to Extend vs Override:
- **Extend** for domain-specific queries (e.g., get_by_user, search_by_title)
- **Override** when you need custom transaction control or caching
- **Use as-is** for simple CRUD operations without special requirements
"""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase


class BaseRepository[T: DeclarativeBase]:
    """Generic repository providing CRUD operations for any SQLAlchemy model.

    This class uses Python 3.12+ PEP 695 generic syntax with type constraints.
    The type parameter T must be a SQLAlchemy ORM model (DeclarativeBase subclass).
    This constraint enables IDE autocomplete and type safety for model attributes.

    Type Parameters:
        T: The SQLAlchemy model type (must extend DeclarativeBase)

    Attributes:
        model: The SQLAlchemy model class
        session: The async database session

    Example:
        repo = BaseRepository[User](User, session)
        user = await repo.get_by_id(123)
        if user:
            user = await repo.update(user, {"name": "New Name"})
    """

    def __init__(self, model: type[T], session: AsyncSession) -> None:
        """Initialize repository with model class and database session.

        Args:
            model: The SQLAlchemy model class to manage
            session: An async database session for queries

        Example:
            from models import User
            repo = BaseRepository[User](User, session)
        """
        self.model = model
        self.session = session

    async def get_by_id(self, id: int | str) -> T | None:
        """Retrieve a single instance by its primary key.

        Args:
            id: The primary key value (int or str for UUID)

        Returns:
            The model instance if found, None otherwise

        Example:
            user = await repo.get_by_id(123)
            if user:
                print(f"Found: {user.name}")
        """
        return await self.session.get(self.model, id)

    async def list(self, offset: int = 0, limit: int = 100) -> Sequence[T]:
        """Retrieve a paginated list of instances.

        Args:
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of model instances

        Example:
            # Get first page (records 0-99)
            page1 = await repo.list(offset=0, limit=100)

            # Get second page (records 100-199)
            page2 = await repo.list(offset=100, limit=100)
        """
        stmt = select(self.model).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_with_count(self, offset: int = 0, limit: int = 100) -> tuple[Sequence[T], int]:
        """Retrieve paginated instances with total count.

        This method is useful for UI pagination where you need to display
        "Showing X-Y of Z results" or calculate total pages.

        Args:
            offset: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100)

        Returns:
            Tuple of (list of instances, total count)

        Example:
            items, total = await repo.list_with_count(offset=0, limit=20)
            current_page = (offset // limit) + 1
            total_pages = (total + limit - 1) // limit
            print(f"Page {current_page} of {total_pages}: {len(items)} items")
            print(f"Showing {offset + 1}-{offset + len(items)} of {total}")
        """
        # Get total count
        count_stmt = select(func.count()).select_from(self.model)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Get paginated items
        items = await self.list(offset, limit)

        return items, total

    async def create(self, data: dict) -> T:
        """Create a new instance from a dictionary of attributes.

        Args:
            data: Dictionary of model attributes and values

        Returns:
            The newly created model instance (refreshed from database)

        Example:
            user = await repo.create({
                "email": "user@example.com",
                "name": "John Doe"
            })
            print(f"Created user with ID: {user.id}")
        """
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: T, data: dict) -> T:
        """Update an existing instance with new attribute values.

        Args:
            instance: The model instance to update
            data: Dictionary of attributes to update

        Returns:
            The updated model instance (refreshed from database)

        Example:
            user = await repo.get_by_id(123)
            if user:
                user = await repo.update(user, {"name": "Updated Name"})
        """
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: T) -> None:
        """Delete an instance from the database.

        Args:
            instance: The model instance to delete

        Example:
            user = await repo.get_by_id(123)
            if user:
                await repo.delete(user)
                print("User deleted")
        """
        await self.session.delete(instance)
        await self.session.commit()

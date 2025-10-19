"""Repository for todo data access operations."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository

from .models import Todo
from .schemas import TodoFilterParams


class TodoRepository(BaseRepository[Todo]):
    """Repository for Todo database operations.

    Extends BaseRepository to provide custom filtering and search capabilities
    for todo items.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session for database operations
        """
        super().__init__(Todo, session)

    async def list_filtered(
        self,
        filters: TodoFilterParams,
    ) -> tuple[Sequence[Todo], int]:
        """Retrieve filtered and sorted todo items with pagination.

        Args:
            filters: Filter and pagination parameters including offset, limit,
                completed status, priority, search term, sort field and order

        Returns:
            Tuple of (filtered items, total count matching filters)

        Example:
            repo = TodoRepository(session)
            filters = TodoFilterParams(
                offset=0,
                limit=20,
                completed=False,
                priority=PriorityEnum.HIGH,
                search="urgent",
                sort_by=SortBy.DUE_DATE,
                sort_order=SortOrder.ASC,
            )
            items, total = await repo.list_filtered(filters)
        """
        # Build base query
        query = select(Todo)

        # Apply filters
        if filters.completed is not None:
            query = query.where(Todo.completed == filters.completed)

        if filters.priority is not None:
            query = query.where(Todo.priority == filters.priority)

        if filters.search is not None:
            search_term = f"%{filters.search}%"
            query = query.where(
                (Todo.title.ilike(search_term)) | (Todo.description.ilike(search_term)),
            )

        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(Todo, filters.sort_by.value, Todo.created_at)
        if filters.sort_order.value.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Apply pagination
        query = query.offset(filters.offset).limit(filters.limit)

        # Execute query
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

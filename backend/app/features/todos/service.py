"""Business logic for todo operations."""

from app.core.exceptions import NotFoundError

from .models import Todo
from .repository import TodoRepository
from .schemas import TodoCreate, TodoFilterParams, TodoUpdate


class TodoService:
    """Service for todo business logic."""

    def __init__(self, repository: TodoRepository) -> None:
        self.repository = repository

    async def create_todo(self, data: TodoCreate) -> Todo:
        """Create a new todo item."""
        todo_dict = data.model_dump()
        return await self.repository.create(todo_dict)

    async def get_todo(self, id: int) -> Todo:
        """Retrieve a todo by ID, raises NotFoundError if not found."""
        todo = await self.repository.get_by_id(id)
        if not todo:
            msg = f"Todo with ID {id} not found"
            raise NotFoundError(msg)
        return todo

    async def list_todos(self, filters: TodoFilterParams) -> tuple[list[Todo], int]:
        """Retrieve filtered and paginated list of todos."""
        items, total = await self.repository.list_filtered(filters)
        return list(items), total

    async def update_todo(self, id: int, data: TodoUpdate) -> Todo:
        """Update an existing todo (partial update, raises NotFoundError if not found)."""
        todo = await self.get_todo(id)
        update_dict = data.model_dump(exclude_unset=True)
        return await self.repository.update(todo, update_dict)

    async def delete_todo(self, id: int) -> None:
        """Delete a todo (raises NotFoundError if not found)."""
        todo = await self.get_todo(id)
        await self.repository.delete(todo)

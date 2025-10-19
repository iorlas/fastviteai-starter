"""FastAPI router for todo endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from .repository import TodoRepository
from .schemas import TodoCreate, TodoFilterParams, TodoListResponse, TodoResponse, TodoUpdate
from .service import TodoService

router = APIRouter(prefix="/api/v1/todos", tags=["todos"])


def get_todo_service(db: Annotated[AsyncSession, Depends(get_db)]) -> TodoService:
    """Dependency injection for TodoService."""
    repository = TodoRepository(db)
    return TodoService(repository)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new todo",
)
async def create_todo(
    data: TodoCreate,
    service: Annotated[TodoService, Depends(get_todo_service)],
) -> TodoResponse:
    return await service.create_todo(data)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List todos with filtering",
)
async def list_todos(
    service: Annotated[TodoService, Depends(get_todo_service)],
    filters: Annotated[TodoFilterParams, Depends()],
) -> TodoListResponse:
    """List todos with filtering, searching, and pagination.

    Query: offset, limit, completed, priority, search, sort_by, sort_order
    """
    items, total = await service.list_todos(filters)

    return TodoListResponse(
        items=[TodoResponse.model_validate(item) for item in items],
        total=total,
        offset=filters.offset,
        limit=filters.limit,
    )


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Get a todo by ID",
)
async def get_todo(
    id: int,
    service: Annotated[TodoService, Depends(get_todo_service)],
) -> TodoResponse:
    return await service.get_todo(id)


@router.patch(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Update a todo",
)
async def update_todo(
    id: int,
    data: TodoUpdate,
    service: Annotated[TodoService, Depends(get_todo_service)],
) -> TodoResponse:
    """Partial update - only provided fields are updated."""
    return await service.update_todo(id, data)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a todo",
)
async def delete_todo(
    id: int,
    service: Annotated[TodoService, Depends(get_todo_service)],
) -> None:
    await service.delete_todo(id)

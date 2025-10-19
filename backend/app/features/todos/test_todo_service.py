"""Unit tests for TodoService."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import NotFoundError
from app.features.todos.models import PriorityEnum, Todo
from app.features.todos.schemas import TodoCreate, TodoFilterParams, TodoUpdate


@pytest.mark.asyncio()
async def test_create_todo(todo_service, mock_repository, sample_todo):
    """Test creating a new todo."""
    # Arrange
    create_data = TodoCreate(
        title="Test Todo",
        description="Test description",
        priority=PriorityEnum.MEDIUM,
        due_date=datetime(2025, 10, 20, 10, 0, 0, tzinfo=UTC),
    )
    mock_repository.create = AsyncMock(return_value=sample_todo)

    # Act
    result = await todo_service.create_todo(create_data)

    # Assert
    mock_repository.create.assert_called_once()
    assert result == sample_todo
    assert result.title == "Test Todo"


@pytest.mark.asyncio()
async def test_get_todo_success(todo_service, mock_repository, sample_todo):
    """Test retrieving an existing todo by ID."""
    # Arrange
    mock_repository.get_by_id = AsyncMock(return_value=sample_todo)

    # Act
    result = await todo_service.get_todo(1)

    # Assert
    mock_repository.get_by_id.assert_called_once_with(1)
    assert result == sample_todo


@pytest.mark.asyncio()
async def test_get_todo_not_found(todo_service, mock_repository):
    """Test retrieving a non-existent todo raises NotFoundError."""
    # Arrange
    mock_repository.get_by_id = AsyncMock(return_value=None)

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await todo_service.get_todo(999)

    assert "999" in str(exc_info.value)
    mock_repository.get_by_id.assert_called_once_with(999)


@pytest.mark.asyncio()
async def test_list_todos(todo_service, mock_repository, sample_todo):
    """Test listing todos with filters."""
    # Arrange
    from app.features.todos.schemas import SortBy, SortOrder

    todos = [sample_todo]
    total = 1
    mock_repository.list_filtered = AsyncMock(return_value=(todos, total))

    filters = TodoFilterParams(
        offset=0,
        limit=100,
        completed=False,
        priority=PriorityEnum.MEDIUM,
        search="test",
        sort_by=SortBy.CREATED_AT,
        sort_order=SortOrder.DESC,
    )

    # Act
    result_items, result_total = await todo_service.list_todos(filters)

    # Assert
    mock_repository.list_filtered.assert_called_once_with(filters)
    assert result_items == todos
    assert result_total == total


@pytest.mark.asyncio()
async def test_update_todo_success(todo_service, mock_repository, sample_todo):
    """Test updating an existing todo."""
    # Arrange
    updated_todo = Todo(
        id=1,
        title="Test Todo",
        description="Test description",
        completed=True,
        priority=PriorityEnum.MEDIUM,
        due_date=datetime(2025, 10, 20, 10, 0, 0, tzinfo=UTC),
        created_at=datetime(2025, 10, 19, 10, 0, 0, tzinfo=UTC),
        updated_at=datetime(2025, 10, 19, 11, 0, 0, tzinfo=UTC),
    )
    mock_repository.get_by_id = AsyncMock(return_value=sample_todo)
    mock_repository.update = AsyncMock(return_value=updated_todo)

    update_data = TodoUpdate(completed=True)

    # Act
    result = await todo_service.update_todo(1, update_data)

    # Assert
    mock_repository.get_by_id.assert_called_once_with(1)
    mock_repository.update.assert_called_once()
    assert result.completed is True


@pytest.mark.asyncio()
async def test_update_todo_not_found(todo_service, mock_repository):
    """Test updating a non-existent todo raises NotFoundError."""
    # Arrange
    mock_repository.get_by_id = AsyncMock(return_value=None)
    update_data = TodoUpdate(completed=True)

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await todo_service.update_todo(999, update_data)

    assert "999" in str(exc_info.value)
    mock_repository.get_by_id.assert_called_once_with(999)
    mock_repository.update.assert_not_called()


@pytest.mark.asyncio()
async def test_delete_todo_success(todo_service, mock_repository, sample_todo):
    """Test deleting an existing todo."""
    # Arrange
    mock_repository.get_by_id = AsyncMock(return_value=sample_todo)
    mock_repository.delete = AsyncMock()

    # Act
    await todo_service.delete_todo(1)

    # Assert
    mock_repository.get_by_id.assert_called_once_with(1)
    mock_repository.delete.assert_called_once_with(sample_todo)


@pytest.mark.asyncio()
async def test_delete_todo_not_found(todo_service, mock_repository):
    """Test deleting a non-existent todo raises NotFoundError."""
    # Arrange
    mock_repository.get_by_id = AsyncMock(return_value=None)

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await todo_service.delete_todo(999)

    assert "999" in str(exc_info.value)
    mock_repository.get_by_id.assert_called_once_with(999)
    mock_repository.delete.assert_not_called()


@pytest.mark.asyncio()
async def test_update_todo_partial(todo_service, mock_repository, sample_todo):
    """Test partial update only updates provided fields."""
    # Arrange
    mock_repository.get_by_id = AsyncMock(return_value=sample_todo)
    mock_repository.update = AsyncMock(return_value=sample_todo)

    # Only update title, leave other fields unchanged
    update_data = TodoUpdate(title="Updated Title")

    # Act
    await todo_service.update_todo(1, update_data)

    # Assert
    call_args = mock_repository.update.call_args
    update_dict = call_args[0][1]
    # Only title should be in the update dict
    assert "title" in update_dict
    assert "completed" not in update_dict
    assert "priority" not in update_dict

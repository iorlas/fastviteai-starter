"""Test fixtures and helpers for todos feature.

Scoped to todos feature only - not shared globally.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.features.todos.models import PriorityEnum, Todo
from app.features.todos.service import TodoService


class TodoTestFactory:
    """Factory for creating test todo instances."""

    @staticmethod
    def create_todo(**overrides):
        """Create a Todo instance with sensible defaults."""
        defaults = {
            "id": 1,
            "title": "Test Todo",
            "description": "Test description",
            "completed": False,
            "priority": PriorityEnum.MEDIUM,
            "due_date": datetime(2025, 10, 20, 10, 0, 0, tzinfo=UTC),
            "created_at": datetime(2025, 10, 19, 10, 0, 0, tzinfo=UTC),
            "updated_at": datetime(2025, 10, 19, 10, 0, 0, tzinfo=UTC),
        }
        return Todo(**{**defaults, **overrides})


@pytest.fixture()
def todo_factory():
    """Provide TodoTestFactory for tests."""
    return TodoTestFactory


@pytest.fixture()
def mock_repository():
    """Create a mock TodoRepository."""
    return MagicMock()


@pytest.fixture()
def todo_service(mock_repository):
    """Create TodoService with mocked repository."""
    return TodoService(mock_repository)


@pytest.fixture()
def sample_todo(todo_factory):
    """Create a sample Todo instance."""
    return todo_factory.create_todo()

"""Pydantic schemas for todo API requests and responses."""

from datetime import datetime
from enum import Enum

from pydantic import ConfigDict, Field

from app.core.base_schema import BaseSchema

from .models import PriorityEnum


class TodoCreate(BaseSchema):
    """Schema for creating a new todo item.

    Attributes:
        title: Todo title (required, max 200 characters)
        description: Optional detailed description
        priority: Priority level (default: medium)
        due_date: Optional due date with timezone
    """

    title: str = Field(..., max_length=200, description="Todo title")
    description: str | None = Field(None, description="Optional detailed description")
    priority: PriorityEnum = Field(PriorityEnum.MEDIUM, description="Priority level")
    due_date: datetime | None = Field(None, description="Optional due date")


class TodoUpdate(BaseSchema):
    """Schema for updating an existing todo item.

    All fields are optional to support partial updates.

    Attributes:
        title: Updated title
        description: Updated description
        completed: Updated completion status
        priority: Updated priority level
        due_date: Updated due date
    """

    title: str | None = Field(None, max_length=200, description="Updated title")
    description: str | None = Field(None, description="Updated description")
    completed: bool | None = Field(None, description="Updated completion status")
    priority: PriorityEnum | None = Field(None, description="Updated priority level")
    due_date: datetime | None = Field(None, description="Updated due date")


class TodoResponse(BaseSchema):
    """Schema for todo item response.

    Attributes:
        id: Unique identifier
        title: Todo title
        description: Optional description
        completed: Completion status
        priority: Priority level
        due_date: Optional due date
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    completed: bool
    priority: PriorityEnum
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime


class TodoListResponse(BaseSchema):
    """Schema for paginated todo list response.

    Attributes:
        items: List of todo items
        total: Total count of items matching filters
        offset: Current offset in the result set
        limit: Maximum number of items per page
    """

    items: list[TodoResponse]
    total: int
    offset: int
    limit: int


class SortOrder(str, Enum):
    """Sort order for todo list queries."""

    ASC = "asc"
    DESC = "desc"


class SortBy(str, Enum):
    """Sort field options for todo list queries."""

    CREATED_AT = "created_at"
    DUE_DATE = "due_date"
    PRIORITY = "priority"
    TITLE = "title"


class TodoFilterParams(BaseSchema):
    """Schema for todo list filtering and pagination query parameters.

    Attributes:
        offset: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 100)
        completed: Filter by completion status
        priority: Filter by priority level
        search: Search term for title and description
        sort_by: Field to sort by (default: created_at)
        sort_order: Sort direction (default: desc)
    """

    offset: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum records to return")
    completed: bool | None = Field(None, description="Filter by completion status")
    priority: PriorityEnum | None = Field(None, description="Filter by priority level")
    search: str | None = Field(None, description="Search term for title and description")
    sort_by: SortBy = Field(SortBy.CREATED_AT, description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort direction")

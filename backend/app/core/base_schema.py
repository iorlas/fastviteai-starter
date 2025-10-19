"""Base schema for all Pydantic models with tech stack quirk handling.

This module provides a base Pydantic model that encapsulates common
validation quirks specific to our FastAPI + HTML forms tech stack.

Key features:
- Automatic empty string to None conversion for datetime fields
- Extensible for other type conversions (int, float, UUID)
- Single source of truth for validation behavior
"""

from datetime import datetime
from typing import Annotated, Any, Union, get_args, get_origin

from pydantic import BaseModel, model_validator


def _is_datetime_type(tp: Any) -> bool:
    """Check if a type annotation is datetime or Optional[datetime].

    Handles:
    - datetime
    - datetime | None (UnionType)
    - Optional[datetime] (Union)
    - Annotated[datetime | None, ...] (Annotated with metadata)

    Args:
        tp: Type annotation to check

    Returns:
        True if the type is datetime or datetime | None (Optional[datetime])

    Examples:
        >>> _is_datetime_type(datetime)
        True
        >>> _is_datetime_type(datetime | None)
        True
        >>> _is_datetime_type(Annotated[datetime | None, Field(...)])
        True
        >>> _is_datetime_type(str)
        False
    """
    if tp is datetime:
        return True
    origin = get_origin(tp)
    # Handle Annotated[datetime | None, ...] - recursively check first arg
    if origin is Annotated:
        args = get_args(tp)
        return _is_datetime_type(args[0]) if args else False
    # Handle both typing.Union (Optional[datetime]) and types.UnionType (datetime | None)
    if origin is Union or str(origin) == "<class 'types.UnionType'>":
        return any(_is_datetime_type(a) for a in get_args(tp))
    return False


class BaseSchema(BaseModel):
    """Base Pydantic schema with automatic validation quirk handling.

    This base class encapsulates common validation behaviors needed for our
    FastAPI + HTML forms tech stack. All request/response schemas should
    inherit from this class.

    Features:
    - **Empty String Conversion**: Automatically converts empty strings to None
      for datetime fields. This handles the common case where HTML forms send
      empty strings for unfilled datetime inputs, but Pydantic expects None
      or a valid datetime.

    Defense-in-Depth Strategy:
    - Frontend should transform empty strings to undefined/null before sending
    - Backend (this class) defensively handles empty strings if they slip through
    - Both layers provide protection against validation errors

    Example:
        >>> class TodoCreate(BaseSchema):
        ...     title: str
        ...     due_date: datetime | None = None
        ...
        >>> # Empty string is converted to None automatically
        >>> todo = TodoCreate(title="Test", due_date="")
        >>> todo.due_date is None
        True

    Extensibility:
    - Add similar conversions for int, float, UUID by extending the validator
    - Keep all tech stack quirks in one place
    """

    @model_validator(mode="before")
    @classmethod
    def _convert_empty_datetime_strings(cls, data: Any) -> Any:
        """Convert empty strings to None for datetime fields.

        This validator runs before field validation and transforms the input data.
        It inspects all fields and converts empty strings to None for any field
        with a datetime type annotation (including Optional[datetime]).

        Args:
            data: Input data (typically a dict from JSON request body)

        Returns:
            Modified data with empty datetime strings converted to None

        Note:
            Only processes dict input. Other input types pass through unchanged.
        """
        if isinstance(data, dict):
            for name, field in cls.model_fields.items():
                if name in data and _is_datetime_type(field.annotation):
                    v = data[name]
                    if isinstance(v, str) and v.strip() == "":
                        data[name] = None
        return data

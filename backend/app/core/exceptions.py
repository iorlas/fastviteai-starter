"""Custom exceptions for domain-specific error handling.

This module defines custom exception classes that represent specific error
conditions in the application. These exceptions are caught by exception handlers
in the main FastAPI application and converted to appropriate HTTP responses.
"""


class NotFoundError(Exception):
    """Raised when a requested resource cannot be found.

    This exception should be used when a client requests a resource (by ID or other
    identifier) that does not exist in the system. The exception handler will convert
    this to a 404 Not Found HTTP response.

    Example:
        raise NotFoundError("User with ID 123 not found")
    """


class ForbiddenError(Exception):
    """Raised when a user attempts an action they don't have permission for.

    This exception should be used when an authenticated user tries to access a
    resource or perform an action that their role/permissions don't allow. The
    exception handler will convert this to a 403 Forbidden HTTP response.

    Example:
        raise ForbiddenError("You do not have permission to delete this resource")
    """


class ValidationError(Exception):
    """Raised when input validation fails.

    This exception should be used for custom validation logic that goes beyond
    Pydantic's automatic validation. The exception handler will convert this to
    a 422 Unprocessable Entity HTTP response.

    Example:
        raise ValidationError("Password must contain at least one special character")
    """

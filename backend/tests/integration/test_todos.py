"""Integration tests for todos feature.

These tests validate HTTP-level validation for the todos API.
Uses defense-in-depth approach where both frontend and backend handle empty strings.

Defense-in-depth strategy:
- Frontend transforms empty strings to undefined/null (first layer)
- Backend BaseSchema converts empty strings to None (second layer)
- Both layers handle the HTML form empty string issue
"""

from fastapi import status
from fastapi.testclient import TestClient


def test_create_todo_with_empty_due_date_string_converted(test_client: TestClient):
    """Test that empty string for optional due_date is CONVERTED to None.

    Defense-in-depth strategy: Both frontend and backend handle empty strings.
    - Frontend transforms empty strings to undefined/null (first layer)
    - Backend BaseSchema converts empty strings to None (second layer)

    Validates:
    - Empty string for due_date is accepted (HTTP 201)
    - Empty string is automatically converted to None by BaseSchema
    - Backend is defensive even if frontend sends empty strings
    """
    response = test_client.post(
        "/api/v1/todos",
        json={
            "title": "Test Todo",
            "description": "",
            "due_date": "",  # Empty string is converted to None
            "priority": "medium",
        },
    )

    # Should succeed (backend converts empty string to None)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["due_date"] is None  # Empty string converted to None
    assert data["priority"] == "medium"


def test_create_todo_with_null_due_date_accepted(test_client: TestClient):
    """Test that null for optional due_date is accepted.

    This is the correct way for frontend to send optional fields.

    Validates:
    - Null is accepted for optional datetime field
    - Todo is created successfully
    """
    response = test_client.post(
        "/api/v1/todos",
        json={
            "title": "Test Todo",
            "description": "",
            "due_date": None,  # Correct: null for optional field
            "priority": "medium",
        },
    )

    # Should succeed
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["due_date"] is None
    assert data["priority"] == "medium"


def test_create_todo_with_invalid_due_date(test_client: TestClient):
    """Test that invalid datetime string is rejected.

    Validates:
    - Invalid datetime format returns validation error (HTTP 422)
    - Error message is descriptive
    """
    response = test_client.post(
        "/api/v1/todos",
        json={
            "title": "Test Todo",
            "due_date": "not-a-date",  # Invalid format
            "priority": "low",
        },
    )

    # Should return validation error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data

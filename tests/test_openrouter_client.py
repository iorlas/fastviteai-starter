"""Test OpenRouter client resource."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

from dagster_project.resources.openrouter_client import OpenRouterClient


@pytest.fixture(scope="module")
def load_env():
    """Load environment variables from .env file."""
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    load_dotenv(env_path)


@pytest.fixture
def mock_context():
    """Create a mock Dagster context."""
    context = MagicMock()
    context.log = MagicMock()
    return context


def test_openrouter_client_initialization(load_env):
    """Test that OpenRouter client can be initialized."""
    client = OpenRouterClient()
    assert client is not None
    assert hasattr(client, "api_key")
    assert hasattr(client, "model")
    assert hasattr(client, "api_endpoint")


def test_openrouter_client_config(load_env):
    """Test OpenRouter client configuration."""
    client = OpenRouterClient()
    assert client.api_endpoint == "https://openrouter.ai/api/v1/chat/completions"
    assert client.model == os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
    assert client.timeout == 30.0


def test_openrouter_client_validation_with_api_key(load_env, mock_context):
    """Test that client validates successfully when API key is present."""
    # Set a test API key
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}):
        client = OpenRouterClient()
        # Should not raise an error
        client.setup_for_execution(mock_context)
        mock_context.log.info.assert_called_once()


def test_openrouter_client_validation_without_api_key(mock_context):
    """Test that client validation fails when API key is missing."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=True):
        client = OpenRouterClient()
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            client.setup_for_execution(mock_context)


def test_chat_completion_request_structure(load_env):
    """Test that chat_completion constructs request correctly."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}):
        client = OpenRouterClient()

        messages = [{"role": "user", "content": "Hello"}]

        with patch("httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"choices": [{"message": {"content": "Hi there"}}]}
            mock_client.return_value.__enter__.return_value.post.return_value = mock_response

            client.chat_completion(messages, temperature=0.5, max_tokens=100)

            # Verify the request was made
            mock_client.return_value.__enter__.return_value.post.assert_called_once()
            call_args = mock_client.return_value.__enter__.return_value.post.call_args

            # Check URL
            assert call_args[0][0] == client.api_endpoint

            # Check payload structure
            payload = call_args[1]["json"]
            assert payload["model"] == client.model
            assert payload["messages"] == messages
            assert payload["temperature"] == 0.5
            assert payload["max_tokens"] == 100


def test_get_completion_text(load_env):
    """Test extracting completion text from response."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}):
        client = OpenRouterClient()

        response = {"choices": [{"message": {"content": "Test response"}}]}

        text = client.get_completion_text(response)
        assert text == "Test response"

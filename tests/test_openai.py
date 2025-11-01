import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

from dagster_project.resources.openai import OpenAIClient


@pytest.fixture(scope="module")
def load_env():
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    load_dotenv(env_path)


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.log = MagicMock()
    return context


def test_openai_client_initialization(load_env):
    client = OpenAIClient()
    assert client is not None
    assert hasattr(client, "api_key")
    assert hasattr(client, "model")
    assert hasattr(client, "base_url")


def test_openai_client_config(load_env):
    client = OpenAIClient()
    assert client.base_url == "https://openrouter.ai/api/v1"
    assert client.model == os.getenv("OPENAI_MODEL", "openai/gpt-4o")
    assert client.timeout == 30.0


def test_openai_client_validation_with_api_key(load_env, mock_context):
    # Set a test API key
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        client = OpenAIClient()
        # Should not raise an error
        client.setup_for_execution(mock_context)
        mock_context.log.info.assert_called_once()


def test_openai_client_initialization_parameters(load_env):
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        with patch("dagster_project.resources.openai.OpenAI") as mock_openai:
            client = OpenAIClient()
            # Access the client property to trigger initialization
            _ = client.client
            # Verify OpenAI client was initialized with correct parameters
            mock_openai.assert_called_once_with(
                api_key="test_key",
                base_url="https://openrouter.ai/api/v1",
                max_retries=3,
                timeout=30.0,
            )


def test_openai_client_validation_without_api_key(mock_context):
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
        client = OpenAIClient()
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            client.setup_for_execution(mock_context)


def test_chat_completion_request_structure(load_env, mock_context):
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        resource = OpenAIClient()

        messages = [{"role": "user", "content": "Hello"}]

        # Create mock response object
        mock_response = MagicMock()
        mock_response.model = "openai/gpt-4o"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hi there"
        mock_response.usage.completion_tokens = 10
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.total_tokens = 15

        # Mock the client property and its method
        with patch.object(resource, "client") as mock_client:
            mock_client.chat.completions.create = MagicMock(return_value=mock_response)

            # Call chat_completion
            response = resource.chat_completion(
                mock_context, messages, temperature=0.5, max_tokens=100
            )

            # Verify the API call was made with correct parameters
            mock_client.chat.completions.create.assert_called_once_with(
                model=resource.model,
                messages=messages,
                temperature=0.5,
                max_tokens=100,
            )

            # Verify debug logging was called
            assert mock_context.log.debug.call_count == 2  # Request and response logging
            assert response == mock_response


def test_get_completion_text(load_env):
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        client = OpenAIClient()

        # Create mock OpenAI response object
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "Test response"

        text = client.get_completion_text(response)
        assert text == "Test response"

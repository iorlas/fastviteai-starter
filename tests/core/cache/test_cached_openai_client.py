import pytest

from dagster_project.core.cache.cached_openai_client import get_cached_openai_client


@pytest.mark.unit
def test_cached_client_creation():
    """Test that OpenAI client is created successfully"""
    client = get_cached_openai_client()

    assert client is not None
    assert hasattr(client, "beta")
    assert hasattr(client.beta, "chat")


@pytest.mark.unit
def test_custom_timeout_parameter():
    """Test that custom timeout parameter is accepted"""
    client = get_cached_openai_client(timeout=60)
    assert client is not None

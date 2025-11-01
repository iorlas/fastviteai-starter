"""Integration test for full project setup."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from dagster_project.definitions import defs
from dagster_project.resources.openrouter_client import OpenRouterClient


@pytest.fixture(scope="module")
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def load_env(project_root):
    """Load environment variables from .env file."""
    env_path = project_root / ".env"
    load_dotenv(env_path)


def test_dagster_definitions_loaded():
    """Test that Dagster definitions are loaded correctly."""
    assert defs is not None
    assert hasattr(defs, "assets")
    assert hasattr(defs, "resources")


def test_openrouter_resource_in_definitions():
    """Test that OpenRouter resource is registered in definitions."""
    assert defs.resources is not None, "defs.resources should not be None"
    assert "openrouter" in defs.resources
    resource = defs.resources["openrouter"]
    assert isinstance(resource, OpenRouterClient)


def test_full_project_structure(project_root):
    """Test that all required directories and files exist."""
    # Check dagster_project structure
    assert (project_root / "dagster_project").exists()
    assert (project_root / "dagster_project" / "definitions.py").exists()
    assert (project_root / "dagster_project" / "assets.py").exists()
    assert (project_root / "dagster_project" / "resources").exists()
    assert (project_root / "dagster_project" / "resources" / "openrouter_client.py").exists()

    # Check storage structure
    assert (project_root / "storage" / "input").exists()
    assert (project_root / "storage" / "input" / "manual_links.txt").exists()
    assert (project_root / "storage" / "input" / "monitoring_list.txt").exists()

    # Check configuration
    assert (project_root / ".env").exists()
    assert (project_root / ".dagster").exists()


def test_environment_configuration(load_env):
    """Test that environment is configured correctly."""
    # All required variables should be set
    assert os.getenv("OPENROUTER_API_KEY") is not None
    assert os.getenv("OPENROUTER_MODEL") == "openai/gpt-4o"
    assert os.getenv("DAGSTER_HOME") is not None

    # DAGSTER_HOME should be absolute
    dagster_home = os.getenv("DAGSTER_HOME")
    assert os.path.isabs(dagster_home)


def test_openrouter_resource_initialization(load_env):
    """Test that OpenRouter resource can be initialized with proper context."""
    # Create a valid API key for testing
    os.environ["OPENROUTER_API_KEY"] = "test_key_for_initialization"

    client = OpenRouterClient()

    # Should initialize without errors
    assert client.base_url == "https://openrouter.ai/api/v1"
    assert client.model in ["openai/gpt-4o", os.getenv("OPENROUTER_MODEL")]
    assert client.timeout == 30.0

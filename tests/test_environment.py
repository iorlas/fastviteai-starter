"""Test environment configuration."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="module")
def load_env():
    """Load environment variables from .env file."""
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    load_dotenv(env_path)


def test_env_file_exists():
    """Test that .env file exists in project root."""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    assert env_file.exists(), ".env file should exist in project root"


def test_environment_variables_loaded(load_env):
    """Test that all required environment variables are set."""
    required_vars = [
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL",
        "DAGSTER_HOME",
    ]

    for var in required_vars:
        value = os.getenv(var)
        assert value is not None, f"Environment variable {var} should be set"
        assert value != "", f"Environment variable {var} should not be empty"


def test_openrouter_model_default(load_env):
    """Test that OPENROUTER_MODEL has the correct default value."""
    model = os.getenv("OPENROUTER_MODEL")
    assert model == "openai/gpt-4o", "Default model should be openai/gpt-4o"


def test_dagster_home_is_absolute(load_env):
    """Test that DAGSTER_HOME is an absolute path."""
    dagster_home = os.getenv("DAGSTER_HOME")
    assert os.path.isabs(dagster_home), "DAGSTER_HOME should be an absolute path"

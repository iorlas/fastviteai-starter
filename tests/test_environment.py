import os
from pathlib import Path

import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="module")
def load_env():
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    load_dotenv(env_path)


def test_env_file_exists():
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    assert env_file.exists(), ".env file should exist in project root"


def test_environment_variables_loaded(load_env):
    required_vars = [
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "DAGSTER_HOME",
    ]

    for var in required_vars:
        value = os.getenv(var)
        assert value is not None, f"Environment variable {var} should be set"
        assert value != "", f"Environment variable {var} should not be empty"


def test_openai_model_default(load_env):
    model = os.getenv("OPENAI_MODEL")
    assert model == "openai/gpt-4o", "Default model should be openai/gpt-4o"


def test_dagster_home_is_absolute(load_env):
    dagster_home = os.getenv("DAGSTER_HOME")
    assert os.path.isabs(dagster_home), "DAGSTER_HOME should be an absolute path"

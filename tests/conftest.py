import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_artifacts_path():
    artifacts_path = Path(__file__).parent.parent / "artifacts"
    os.environ["ARTIFACTS_PATH"] = str(artifacts_path)
    yield
    del os.environ["ARTIFACTS_PATH"]


@pytest.fixture(scope="module")
def artifacts_path():
    return Path(os.environ["ARTIFACTS_PATH"])

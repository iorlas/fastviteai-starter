import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_project_root():
    project_root = Path(__file__).parent.parent
    os.environ["PROJECT_ROOT"] = str(project_root)
    yield
    del os.environ["PROJECT_ROOT"]


@pytest.fixture(scope="module")
def project_root():
    return Path(os.environ["PROJECT_ROOT"])

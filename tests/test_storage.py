from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def project_root():
    return Path(__file__).parent.parent


def test_storage_directory_exists(project_root):
    storage_dir = project_root / "storage"
    assert storage_dir.exists(), "storage directory should exist"
    assert storage_dir.is_dir(), "storage should be a directory"


def test_input_directory_exists(project_root):
    input_dir = project_root / "storage" / "input"
    assert input_dir.exists(), "storage/input directory should exist"
    assert input_dir.is_dir(), "storage/input should be a directory"


def test_manual_links_file_exists(project_root):
    manual_links = project_root / "storage" / "input" / "manual_links.txt"
    assert manual_links.exists(), "manual_links.txt should exist"
    assert manual_links.is_file(), "manual_links.txt should be a file"


def test_monitoring_list_file_exists(project_root):
    monitoring_list = project_root / "storage" / "input" / "monitoring_list.txt"
    assert monitoring_list.exists(), "monitoring_list.txt should exist"
    assert monitoring_list.is_file(), "monitoring_list.txt should be a file"

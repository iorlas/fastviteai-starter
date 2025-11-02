import json
from pathlib import Path

import pytest

from dagster_project.resources.io_managers import BronzeIOManager


@pytest.mark.integration
def test_integration_link_list_bronze_storage():
    from dagster import OutputContext

    bronze_io_manager = BronzeIOManager()

    link_list = [
        "https://example.com/article1",
        "https://example.com/article2",
    ]

    context = OutputContext(
        name="test_output",
        step_key="test_step",
        mapping_key=None,
        config=None,
        metadata=None,
        log_manager=None,
        version=None,
        resource_config=None,
        resources=None,
        dagster_type=None,
        asset_key=None,
    )

    bronze_io_manager.handle_output(context, link_list)

    bronze_links_dir = Path("artifacts/bronze/raw_links")
    assert bronze_links_dir.exists()

    files = list(bronze_links_dir.glob("*.json"))
    assert len(files) >= 1

    latest_file = sorted(files)[-1]

    with latest_file.open() as f:
        data = json.load(f)

    assert "links" in data
    assert "created_at" in data
    assert len(data["links"]) == 2
    assert set(data["links"]) == set(link_list)

    assert len(latest_file.stem) == 64


@pytest.mark.integration
def test_integration_html_bronze_storage():
    from dagster import OutputContext

    bronze_io_manager = BronzeIOManager()

    html_data = {
        "url": "https://example.com/test-article",
        "html_content": "<html><head><title>Test</title></head><body>Content</body></html>",
        "download_info": {"status_code": 200, "content_type": "text/html"},
    }

    context = OutputContext(
        name="test_output",
        step_key="test_step",
        mapping_key=None,
        config=None,
        metadata=None,
        log_manager=None,
        version=None,
        resource_config=None,
        resources=None,
        dagster_type=None,
        asset_key=None,
    )

    bronze_io_manager.handle_output(context, html_data)

    bronze_html_dir = Path("artifacts/bronze/raw_html")
    assert bronze_html_dir.exists()

    files = list(bronze_html_dir.glob("*.json"))
    assert len(files) >= 1

    latest_file = sorted(files)[-1]

    with latest_file.open() as f:
        data = json.load(f)

    assert data["url"] == html_data["url"]
    assert data["content"] == html_data["html_content"]
    assert "created_at" in data
    assert "content_length" in data
    assert "download_info" in data

    assert len(latest_file.stem) == 64


@pytest.mark.integration
def test_integration_bronze_storage_verification():
    bronze_dir = Path("artifacts/bronze")
    raw_links_dir = bronze_dir / "raw_links"
    raw_html_dir = bronze_dir / "raw_html"

    assert bronze_dir.exists()
    assert raw_links_dir.exists()
    assert raw_html_dir.exists()

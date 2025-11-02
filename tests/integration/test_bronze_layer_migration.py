import hashlib
import json
from unittest.mock import PropertyMock

import pytest
from dagster import build_asset_context

from dagster_project.assets.bronze_raw_links import bronze_raw_links
from dagster_project.resources.io_managers import BronzeIOManager


@pytest.fixture
def bronze_test_env(tmp_path):
    # Create input files
    manual_file = tmp_path / "manual_links.txt"
    manual_file.write_text(
        "https://example.com/bronze-manual-1\n"
        "https://example.com/bronze-manual-2\n"
        "https://example.com/bronze-manual-3\n"
    )

    monitoring_file = tmp_path / "monitoring_list.txt"
    monitoring_file.write_text(
        "https://example.com/bronze-monitoring-1\nhttps://example.com/bronze-monitoring-2\n"
    )

    # Create artifact directories
    (tmp_path / "artifacts" / "summaries").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "bronze" / "raw_links").mkdir(parents=True, exist_ok=True)

    return tmp_path


@pytest.mark.integration
def test_bronze_raw_links_storage_with_iomanager(bronze_test_env):
    # Create BronzeIOManager pointing to test directory
    bronze_io_manager = BronzeIOManager(base_dir=str(bronze_test_env / "artifacts" / "bronze"))

    # Create asset execution context
    context = build_asset_context()
    type(context).op_config = PropertyMock(
        return_value={"source_filter": "both", "project_root": str(bronze_test_env)}
    )

    # Execute bronze_raw_links asset
    links = bronze_raw_links(context)

    # Should have 5 unprocessed links (3 manual + 2 monitoring)
    assert len(links) == 5
    assert all(isinstance(link, str) for link in links)

    # Simulate IOManager saving the output
    from dagster import OutputContext

    output_context = OutputContext(
        name="bronze_raw_links",
        step_key="bronze_raw_links",
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

    bronze_io_manager.handle_output(output_context, links)

    # Verify files created in bronze/raw_links/
    raw_links_dir = bronze_test_env / "artifacts" / "bronze" / "raw_links"
    json_files = list(raw_links_dir.glob("*.json"))

    assert len(json_files) == 1

    # Verify filename uses full SHA256 hash (64 chars)
    json_file = json_files[0]
    assert len(json_file.stem) == 64

    # Verify JSON structure
    with json_file.open() as f:
        data = json.load(f)

    assert "links" in data
    assert "created_at" in data
    assert "link_count" in data
    assert data["link_count"] == 5
    assert len(data["links"]) == 5


@pytest.mark.integration
def test_bronze_raw_links_hash_determinism(bronze_test_env):
    # Create BronzeIOManager
    bronze_io_manager = BronzeIOManager(base_dir=str(bronze_test_env / "artifacts" / "bronze"))

    # Create same link list twice
    links = [
        "https://example.com/test-1",
        "https://example.com/test-2",
        "https://example.com/test-3",
    ]

    from dagster import OutputContext

    output_context = OutputContext(
        name="bronze_raw_links",
        step_key="bronze_raw_links",
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

    # Save first time
    bronze_io_manager.handle_output(output_context, links)

    raw_links_dir = bronze_test_env / "artifacts" / "bronze" / "raw_links"
    files_after_first = list(raw_links_dir.glob("*.json"))
    assert len(files_after_first) == 1
    first_hash = files_after_first[0].stem

    # Save second time with same links (should overwrite, not create new file)
    bronze_io_manager.handle_output(output_context, links)

    files_after_second = list(raw_links_dir.glob("*.json"))
    assert len(files_after_second) == 1
    second_hash = files_after_second[0].stem

    # Hash should be the same (deterministic)
    assert first_hash == second_hash
    assert len(first_hash) == 64


@pytest.mark.integration
def test_bronze_raw_links_manual_filter(bronze_test_env):
    # Test that manual filter only processes manual_links.txt
    context = build_asset_context()
    type(context).op_config = PropertyMock(
        return_value={"source_filter": "manual", "project_root": str(bronze_test_env)}
    )

    links = bronze_raw_links(context)

    assert len(links) == 3
    assert all("bronze-manual" in link for link in links)


@pytest.mark.integration
def test_bronze_raw_links_monitoring_filter(bronze_test_env):
    # Test that monitoring filter only processes monitoring_list.txt
    context = build_asset_context()
    type(context).op_config = PropertyMock(
        return_value={"source_filter": "monitoring", "project_root": str(bronze_test_env)}
    )

    links = bronze_raw_links(context)

    assert len(links) == 2
    assert all("bronze-monitoring" in link for link in links)


@pytest.mark.integration
def test_bronze_raw_links_deduplication(bronze_test_env):
    # Create a summary file for one URL to test deduplication
    summaries_dir = bronze_test_env / "artifacts" / "summaries"

    # Compute hash for one of the manual links
    test_url = "https://example.com/bronze-manual-1"
    url_hash = hashlib.sha256(test_url.encode()).hexdigest()[:16]
    summary_file = summaries_dir / f"{url_hash}.json"

    # Create a fake summary file
    summary_file.write_text('{"url": "https://example.com/bronze-manual-1", "summary": "test"}')

    # Run bronze_raw_links
    context = build_asset_context()
    type(context).op_config = PropertyMock(
        return_value={"source_filter": "both", "project_root": str(bronze_test_env)}
    )

    links = bronze_raw_links(context)

    # Should have 4 links instead of 5 (one was already processed)
    assert len(links) == 4
    assert test_url not in links

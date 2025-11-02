import hashlib
import json
from datetime import datetime

import pytest

from dagster_project.resources.io_managers import BronzeIOManager


@pytest.fixture
def bronze_io_manager(tmp_path):
    return BronzeIOManager(base_dir=str(tmp_path / "bronze"))


@pytest.mark.integration
def test_bronze_io_manager_class_exists():
    from dagster import IOManager

    assert issubclass(BronzeIOManager, IOManager)


@pytest.mark.integration
def test_link_list_serialization_round_trip(bronze_io_manager, tmp_path):
    from dagster import OutputContext

    link_list = [
        "https://example.com/article1",
        "https://example.com/article2",
        "https://example.com/article3",
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

    files = list(bronze_io_manager.raw_links_dir.glob("*.json"))
    assert len(files) == 1

    with files[0].open() as f:
        data = json.load(f)

    assert "links" in data
    assert "created_at" in data
    assert "link_count" in data
    assert set(data["links"]) == set(link_list)
    assert data["link_count"] == 3


@pytest.mark.integration
def test_html_content_storage_with_metadata(bronze_io_manager, tmp_path):
    from dagster import OutputContext

    html_data = {
        "url": "https://example.com/article",
        "html_content": "<html><body>Test content</body></html>",
        "download_info": {"status_code": 200, "headers": {"content-type": "text/html"}},
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

    files = list(bronze_io_manager.raw_html_dir.glob("*.json"))
    assert len(files) == 1

    with files[0].open() as f:
        data = json.load(f)

    assert data["url"] == html_data["url"]
    assert data["content"] == html_data["html_content"]
    assert "created_at" in data
    assert "content_length" in data
    assert data["content_length"] == len(html_data["html_content"])
    assert "download_info" in data


@pytest.mark.integration
def test_sha256_hash_generation_consistency(bronze_io_manager):
    url = "https://example.com/test"

    hash1 = hashlib.sha256(url.encode()).hexdigest()
    hash2 = hashlib.sha256(url.encode()).hexdigest()

    assert hash1 == hash2
    assert len(hash1) == 64
    assert len(hash2) == 64


@pytest.mark.integration
def test_created_at_timestamp_format(bronze_io_manager, tmp_path):
    from dagster import OutputContext

    link_list = ["https://example.com/test"]

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

    files = list(bronze_io_manager.raw_links_dir.glob("*.json"))
    with files[0].open() as f:
        data = json.load(f)

    assert "created_at" in data
    timestamp_str = data["created_at"]

    parsed_timestamp = datetime.fromisoformat(timestamp_str)
    assert isinstance(parsed_timestamp, datetime)


@pytest.mark.integration
def test_error_handling_missing_files(bronze_io_manager):
    from dagster import AssetKey, InputContext

    context = InputContext(
        name="test_input",
        upstream_output=None,
        dagster_type=None,
        config=None,
        metadata=None,
        log_manager=None,
        resource_config=None,
        resources=None,
        asset_key=AssetKey(["bronze_raw_links"]),
    )

    result = bronze_io_manager.load_input(context)
    assert result == []


@pytest.mark.integration
def test_metadata_preservation_across_save_load_cycle(bronze_io_manager):
    from dagster import AssetKey, InputContext, OutputContext

    html_data = {
        "url": "https://example.com/test",
        "html_content": "<html><body>Test</body></html>",
        "download_info": {"status_code": 200},
    }

    output_context = OutputContext(
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

    bronze_io_manager.handle_output(output_context, html_data)

    input_context = InputContext(
        name="test_input",
        upstream_output=type("MockUpstream", (), {"asset_key": AssetKey(["bronze_raw_html"])})(),
        dagster_type=None,
        config=None,
        metadata=None,
        log_manager=None,
        resource_config=None,
        resources=None,
        asset_key=AssetKey(["bronze_raw_html"]),
    )

    loaded_data = bronze_io_manager.load_input(input_context)

    assert loaded_data["url"] == html_data["url"]
    assert loaded_data["content"] == html_data["html_content"]
    assert "created_at" in loaded_data
    assert "download_info" in loaded_data


@pytest.mark.integration
def test_handle_output_invalid_type_raises_error(bronze_io_manager):
    from dagster import OutputContext

    invalid_data = "this is a string, not list or dict"

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

    with pytest.raises(TypeError, match="BronzeIOManager cannot handle type"):
        bronze_io_manager.handle_output(context, invalid_data)


@pytest.mark.integration
def test_handle_output_dict_without_html_content_raises_error(bronze_io_manager):
    from dagster import OutputContext

    invalid_data = {"some_key": "some_value", "no_html_content_key": True}

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

    with pytest.raises(TypeError, match="BronzeIOManager cannot handle type"):
        bronze_io_manager.handle_output(context, invalid_data)


@pytest.mark.integration
def test_handle_output_html_missing_url_field(bronze_io_manager):
    from dagster import OutputContext

    malformed_html_data = {
        "html_content": "<html><body>Test</body></html>",
        "download_info": {"status_code": 200},
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

    with pytest.raises(KeyError):
        bronze_io_manager.handle_output(context, malformed_html_data)


@pytest.mark.integration
def test_load_input_unknown_asset_key(bronze_io_manager):
    from dagster import AssetKey, InputContext

    context = InputContext(
        name="test_input",
        upstream_output=type("MockUpstream", (), {"asset_key": AssetKey(["unknown_asset"])})(),
        dagster_type=None,
        config=None,
        metadata=None,
        log_manager=None,
        resource_config=None,
        resources=None,
        asset_key=AssetKey(["unknown_asset"]),
    )

    with pytest.raises(TypeError, match="BronzeIOManager cannot load asset"):
        bronze_io_manager.load_input(context)


@pytest.mark.integration
def test_load_input_link_list_with_corrupted_json(bronze_io_manager, tmp_path):
    from dagster import AssetKey, InputContext

    corrupted_file = bronze_io_manager.raw_links_dir / "test_hash.json"
    corrupted_file.parent.mkdir(parents=True, exist_ok=True)
    with corrupted_file.open("w") as f:
        f.write("{invalid json content")

    context = InputContext(
        name="test_input",
        upstream_output=type("MockUpstream", (), {"asset_key": AssetKey(["bronze_raw_links"])})(),
        dagster_type=None,
        config=None,
        metadata=None,
        log_manager=None,
        resource_config=None,
        resources=None,
        asset_key=AssetKey(["bronze_raw_links"]),
    )

    result = bronze_io_manager.load_input(context)
    assert result == []


@pytest.mark.integration
def test_load_input_html_with_corrupted_json(bronze_io_manager, tmp_path):
    from dagster import AssetKey, InputContext

    corrupted_file = bronze_io_manager.raw_html_dir / "test_hash.json"
    corrupted_file.parent.mkdir(parents=True, exist_ok=True)
    with corrupted_file.open("w") as f:
        f.write("not valid json at all")

    context = InputContext(
        name="test_input",
        upstream_output=type("MockUpstream", (), {"asset_key": AssetKey(["bronze_raw_html"])})(),
        dagster_type=None,
        config=None,
        metadata=None,
        log_manager=None,
        resource_config=None,
        resources=None,
        asset_key=AssetKey(["bronze_raw_html"]),
    )

    result = bronze_io_manager.load_input(context)
    assert result == {}


@pytest.mark.integration
def test_load_input_link_list_success(bronze_io_manager):
    from dagster import AssetKey, InputContext, OutputContext

    link_list = ["https://example.com/1", "https://example.com/2"]

    output_context = OutputContext(
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

    bronze_io_manager.handle_output(output_context, link_list)

    input_context = InputContext(
        name="test_input",
        upstream_output=type("MockUpstream", (), {"asset_key": AssetKey(["bronze_raw_links"])})(),
        dagster_type=None,
        config=None,
        metadata=None,
        log_manager=None,
        resource_config=None,
        resources=None,
        asset_key=AssetKey(["bronze_raw_links"]),
    )

    loaded_links = bronze_io_manager.load_input(input_context)
    assert isinstance(loaded_links, list)
    assert set(loaded_links) == set(link_list)

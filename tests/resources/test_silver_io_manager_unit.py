import hashlib
import json
from datetime import datetime

import pytest
from dagster import OutputContext

from dagster_project.resources.io_managers import SilverIOManager


@pytest.fixture
def silver_io_manager(tmp_path):
    return SilverIOManager(base_dir=str(tmp_path / "silver"))


@pytest.mark.integration
def test_silver_io_manager_class_exists():
    from dagster_project.resources.io_managers import SilverIOManager

    assert SilverIOManager is not None


@pytest.mark.integration
def test_extracted_content_html_storage(silver_io_manager, tmp_path):
    content_data = {
        "url": "https://example.com/article",
        "type": "html",
        "title": "Test Article",
        "content": "Article content here",
        "metadata": {
            "author": "Test Author",
            "word_count": 100,
        },
        "lineage": {
            "source_asset": "bronze_raw_html",
            "source_hash": "abc123",
            "transformation_timestamp": "2025-11-02T12:00:00Z",
        },
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

    silver_io_manager.handle_output(context, content_data)

    extracted_content_dir = tmp_path / "silver" / "extracted_content"
    assert extracted_content_dir.exists()

    files = list(extracted_content_dir.glob("*.json"))
    assert len(files) == 1

    with files[0].open() as f:
        data = json.load(f)

    assert data["url"] == content_data["url"]
    assert data["type"] == "html"
    assert data["title"] == content_data["title"]
    assert data["content"] == content_data["content"]
    assert "created_at" in data
    assert "updated_at" in data
    assert "lineage" in data
    assert len(files[0].stem) == 64


@pytest.mark.integration
def test_extracted_content_video_storage(silver_io_manager, tmp_path):
    content_data = {
        "url": "https://youtube.com/watch?v=123",
        "type": "youtube",
        "title": "Test Video",
        "content": "Video description",
        "metadata": {
            "extraction_method": "yt-dlp",
        },
        "lineage": {
            "source_asset": "bronze_raw_html",
            "source_hash": "def456",
            "transformation_timestamp": "2025-11-02T12:00:00Z",
        },
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

    silver_io_manager.handle_output(context, content_data)

    extracted_content_dir = tmp_path / "silver" / "extracted_content"
    files = list(extracted_content_dir.glob("*.json"))
    assert len(files) == 1

    with files[0].open() as f:
        data = json.load(f)

    assert data["type"] == "youtube"
    assert data["title"] == content_data["title"]


@pytest.mark.integration
def test_summary_success_dual_format(silver_io_manager, tmp_path):
    summary_data = {
        "url": "https://example.com/article",
        "status": "success",
        "summary": "- Point 1\n- Point 2\n- Point 3",
        "model": "openai/gpt-4o",
        "tokens_used": 150,
        "latency_ms": 1200,
        "lineage": {
            "source_asset": "silver_extracted_content",
            "source_hash": "xyz789",
            "transformation_timestamp": "2025-11-02T12:00:00Z",
        },
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

    silver_io_manager.handle_output(context, summary_data)

    summaries_dir = tmp_path / "silver" / "summaries"
    assert summaries_dir.exists()

    json_files = list(summaries_dir.glob("*.json"))
    md_files = list(summaries_dir.glob("*.md"))

    assert len(json_files) == 1
    assert len(md_files) == 1
    assert json_files[0].stem == md_files[0].stem
    assert len(json_files[0].stem) == 64

    with json_files[0].open() as f:
        json_data = json.load(f)

    assert json_data["status"] == "success"
    assert json_data["summary"] == summary_data["summary"]
    assert json_data["model"] == summary_data["model"]
    assert "created_at" in json_data
    assert "updated_at" in json_data

    md_content = md_files[0].read_text()
    assert "Success" in md_content
    assert summary_data["url"] in md_content
    assert summary_data["summary"] in md_content
    assert summary_data["model"] in md_content


@pytest.mark.integration
def test_summary_failure_dual_format(silver_io_manager, tmp_path):
    summary_data = {
        "url": "https://example.com/article",
        "status": "failed",
        "error": "API timeout",
        "error_type": "TimeoutError",
        "lineage": {
            "source_asset": "silver_extracted_content",
            "source_hash": "xyz789",
            "transformation_timestamp": "2025-11-02T12:00:00Z",
        },
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

    silver_io_manager.handle_output(context, summary_data)

    summaries_dir = tmp_path / "silver" / "summaries"
    md_files = list(summaries_dir.glob("*.md"))

    md_content = md_files[0].read_text()
    assert "Failed" in md_content
    assert summary_data["error"] in md_content
    assert summary_data["error_type"] in md_content


@pytest.mark.integration
def test_sha256_hash_consistency(silver_io_manager, tmp_path):
    content_data1 = {
        "url": "https://example.com/same-url",
        "type": "html",
        "title": "Test",
        "content": "Content 1",
    }

    content_data2 = {
        "url": "https://example.com/same-url",
        "type": "html",
        "title": "Test",
        "content": "Content 2",
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

    silver_io_manager.handle_output(context, content_data1)
    silver_io_manager.handle_output(context, content_data2)

    extracted_content_dir = tmp_path / "silver" / "extracted_content"
    files = list(extracted_content_dir.glob("*.json"))
    assert len(files) == 1


@pytest.mark.integration
def test_timestamps_iso8601_format(silver_io_manager, tmp_path):
    content_data = {
        "url": "https://example.com/test",
        "type": "html",
        "title": "Test",
        "content": "Content",
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

    silver_io_manager.handle_output(context, content_data)

    extracted_content_dir = tmp_path / "silver" / "extracted_content"
    files = list(extracted_content_dir.glob("*.json"))

    with files[0].open() as f:
        data = json.load(f)

    assert "created_at" in data
    assert "updated_at" in data
    assert "T" in data["created_at"]
    assert ":" in data["created_at"]


@pytest.mark.integration
def test_lineage_metadata_structure(silver_io_manager, tmp_path):
    content_data = {
        "url": "https://example.com/test",
        "type": "html",
        "title": "Test",
        "content": "Content",
        "lineage": {
            "source_asset": "bronze_raw_html",
            "source_hash": "abc123def456",
            "transformation_timestamp": "2025-11-02T12:00:00Z",
        },
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

    silver_io_manager.handle_output(context, content_data)

    extracted_content_dir = tmp_path / "silver" / "extracted_content"
    files = list(extracted_content_dir.glob("*.json"))

    with files[0].open() as f:
        data = json.load(f)

    assert "lineage" in data
    assert data["lineage"]["source_asset"] == "bronze_raw_html"
    assert data["lineage"]["source_hash"] == "abc123def456"
    assert "transformation_timestamp" in data["lineage"]


@pytest.mark.integration
def test_error_handling_missing_files(silver_io_manager, tmp_path):
    from dagster import InputContext

    context = InputContext(
        name="test_input",
        upstream_output=None,
        dagster_type=None,
        resource_config=None,
        resources=None,
        asset_key=None,
    )

    result = silver_io_manager._load_input_extracted_content(context)
    assert result == {}


@pytest.mark.integration
def test_metadata_preservation_round_trip(silver_io_manager, tmp_path):
    original_data = {
        "url": "https://example.com/test",
        "type": "html",
        "title": "Test Article",
        "content": "Test content",
        "metadata": {
            "author": "Test Author",
            "word_count": 500,
        },
        "lineage": {
            "source_asset": "bronze_raw_html",
            "source_hash": "test_hash",
            "transformation_timestamp": "2025-11-02T12:00:00Z",
        },
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

    silver_io_manager.handle_output(context, original_data)

    extracted_content_dir = tmp_path / "silver" / "extracted_content"
    files = list(extracted_content_dir.glob("*.json"))

    with files[0].open() as f:
        loaded_data = json.load(f)

    assert loaded_data["url"] == original_data["url"]
    assert loaded_data["type"] == original_data["type"]
    assert loaded_data["title"] == original_data["title"]
    assert loaded_data["content"] == original_data["content"]
    assert loaded_data["metadata"] == original_data["metadata"]
    assert loaded_data["lineage"]["source_asset"] == original_data["lineage"].get("source_asset")


@pytest.mark.integration
def test_error_handling_invalid_content_type(silver_io_manager):
    invalid_content = {
        "url": "https://example.com/invalid",
        "type": "pdf",
        "title": "Invalid Type",
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

    with pytest.raises(TypeError, match="SilverIOManager cannot handle type"):
        silver_io_manager.handle_output(context, invalid_content)


@pytest.mark.integration
def test_error_handling_missing_required_fields(silver_io_manager):
    missing_url = {
        "type": "html",
        "title": "No URL",
        "content": "Content without URL",
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
        silver_io_manager.handle_output(context, missing_url)


@pytest.mark.integration
def test_error_handling_unknown_asset_key(silver_io_manager):
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

    with pytest.raises(TypeError, match="SilverIOManager cannot load asset"):
        silver_io_manager.load_input(context)


@pytest.mark.integration
def test_error_handling_non_dict_items_in_list(silver_io_manager):
    invalid_list = ["string1", "string2", "string3"]

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

    with pytest.raises(TypeError, match="SilverIOManager cannot handle list item type"):
        silver_io_manager.handle_output(context, invalid_list)


@pytest.mark.integration
def test_error_handling_corrupted_json_extracted_content(silver_io_manager, tmp_path):
    from dagster import AssetKey, InputContext

    corrupted_file = tmp_path / "silver" / "extracted_content" / "corrupted.json"
    corrupted_file.parent.mkdir(parents=True, exist_ok=True)
    with corrupted_file.open("w") as f:
        f.write("{invalid json content")

    context = InputContext(
        name="test_input",
        upstream_output=type(
            "MockUpstream", (), {"asset_key": AssetKey(["silver_extracted_content"])}
        )(),
        dagster_type=None,
        config=None,
        metadata=None,
        log_manager=None,
        resource_config=None,
        resources=None,
        asset_key=AssetKey(["silver_extracted_content"]),
    )

    result = silver_io_manager.load_input(context)
    assert result == {}


@pytest.mark.integration
def test_error_handling_corrupted_json_summary(silver_io_manager, tmp_path):
    from dagster import AssetKey, InputContext

    corrupted_file = tmp_path / "silver" / "summaries" / "corrupted.json"
    corrupted_file.parent.mkdir(parents=True, exist_ok=True)
    with corrupted_file.open("w") as f:
        f.write("not valid json")

    context = InputContext(
        name="test_input",
        upstream_output=type("MockUpstream", (), {"asset_key": AssetKey(["silver_summaries"])})(),
        dagster_type=None,
        config=None,
        metadata=None,
        log_manager=None,
        resource_config=None,
        resources=None,
        asset_key=AssetKey(["silver_summaries"]),
    )

    result = silver_io_manager.load_input(context)
    assert result == {}


@pytest.mark.integration
def test_load_input_extracted_content_success(silver_io_manager):
    from dagster import AssetKey, InputContext

    content = {
        "url": "https://example.com/load-test",
        "type": "html",
        "title": "Load Test",
        "content": "Content to load",
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

    silver_io_manager.handle_output(output_context, content)

    input_context = InputContext(
        name="test_input",
        upstream_output=type(
            "MockUpstream", (), {"asset_key": AssetKey(["silver_extracted_content"])}
        )(),
        dagster_type=None,
        config=None,
        metadata=None,
        log_manager=None,
        resource_config=None,
        resources=None,
        asset_key=AssetKey(["silver_extracted_content"]),
    )

    loaded_data = silver_io_manager.load_input(input_context)

    assert loaded_data["url"] == content["url"]
    assert loaded_data["type"] == content["type"]
    assert loaded_data["title"] == content["title"]


@pytest.mark.integration
def test_load_input_summary_success(silver_io_manager):
    from dagster import AssetKey, InputContext

    summary = {
        "url": "https://example.com/summary-load",
        "title": "Summary Load Test",
        "status": "success",
        "summary": "Test summary content",
        "model": "openai/gpt-4o",
        "tokens_used": 500,
        "latency_ms": 1000,
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

    silver_io_manager.handle_output(output_context, summary)

    input_context = InputContext(
        name="test_input",
        upstream_output=type("MockUpstream", (), {"asset_key": AssetKey(["silver_summaries"])})(),
        dagster_type=None,
        config=None,
        metadata=None,
        log_manager=None,
        resource_config=None,
        resources=None,
        asset_key=AssetKey(["silver_summaries"]),
    )

    loaded_data = silver_io_manager.load_input(input_context)

    assert loaded_data["url"] == summary["url"]
    assert loaded_data["status"] == "success"
    assert loaded_data["summary"] == summary["summary"]


@pytest.mark.integration
def test_sha256_hash_64_chars(silver_io_manager):
    url = "https://example.com/test-article"

    hash_value = hashlib.sha256(url.encode()).hexdigest()

    assert len(hash_value) == 64


@pytest.mark.integration
def test_timestamp_iso8601_validation(silver_io_manager, tmp_path):
    content_data = {
        "url": "https://example.com/timestamp",
        "type": "html",
        "title": "Timestamp Test",
        "content": "Content",
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

    silver_io_manager.handle_output(context, content_data)

    extracted_content_dir = tmp_path / "silver" / "extracted_content"
    files = list(extracted_content_dir.glob("*.json"))

    with files[0].open() as f:
        data = json.load(f)

    created_at = datetime.fromisoformat(data["created_at"])
    updated_at = datetime.fromisoformat(data["updated_at"])

    assert isinstance(created_at, datetime)
    assert isinstance(updated_at, datetime)

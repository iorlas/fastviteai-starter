import json
from pathlib import Path

import pytest

from dagster_project.resources.io_managers import SilverIOManager


@pytest.mark.integration
def test_integration_extracted_content_html_storage():
    import hashlib

    from dagster import OutputContext

    silver_io_manager = SilverIOManager()

    html_url = "https://example.com/unique_html_article_test"
    content_data = {
        "url": html_url,
        "type": "html",
        "title": "Test HTML Article",
        "content": "HTML article content",
        "metadata": {
            "author": "Test Author",
            "word_count": 200,
        },
        "lineage": {
            "source_asset": "bronze_raw_html",
            "source_hash": "html_test_hash",
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

    silver_extracted_content_dir = Path("artifacts/silver/extracted_content")
    assert silver_extracted_content_dir.exists()

    expected_hash = hashlib.sha256(html_url.encode()).hexdigest()
    expected_file = silver_extracted_content_dir / f"{expected_hash}.json"

    assert expected_file.exists()
    assert len(expected_file.stem) == 64

    with expected_file.open() as f:
        data = json.load(f)

    assert data["url"] == content_data["url"]
    assert data["type"] == "html"
    assert data["title"] == content_data["title"]
    assert data["content"] == content_data["content"]
    assert "created_at" in data
    assert "updated_at" in data
    assert "lineage" in data


@pytest.mark.integration
def test_integration_extracted_content_video_storage():
    import hashlib

    from dagster import OutputContext

    silver_io_manager = SilverIOManager()

    video_url = "https://youtube.com/watch?v=unique_video_test_123"
    content_data = {
        "url": video_url,
        "type": "youtube",
        "title": "Test Video Title",
        "content": "Video description content",
        "metadata": {
            "extraction_method": "yt-dlp",
        },
        "lineage": {
            "source_asset": "bronze_raw_html",
            "source_hash": "video_test_hash",
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

    silver_extracted_content_dir = Path("artifacts/silver/extracted_content")
    assert silver_extracted_content_dir.exists()

    expected_hash = hashlib.sha256(video_url.encode()).hexdigest()
    expected_file = silver_extracted_content_dir / f"{expected_hash}.json"

    assert expected_file.exists()
    assert len(expected_file.stem) == 64

    with expected_file.open() as f:
        data = json.load(f)

    assert data["type"] == "youtube"
    assert data["title"] == content_data["title"]


@pytest.mark.integration
def test_integration_summary_dual_format_storage():
    import hashlib

    from dagster import OutputContext

    silver_io_manager = SilverIOManager()

    test_url = "https://example.com/summary-test-unique-123"
    summary_data = {
        "url": test_url,
        "status": "success",
        "summary": "- Key point 1\n- Key point 2\n- Key point 3",
        "model": "openai/gpt-4o",
        "tokens_used": 200,
        "latency_ms": 1500,
        "lineage": {
            "source_asset": "silver_extracted_content",
            "source_hash": "summary_test_hash",
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

    silver_summaries_dir = Path("artifacts/silver/summaries")
    assert silver_summaries_dir.exists()

    expected_hash = hashlib.sha256(test_url.encode()).hexdigest()
    json_path = silver_summaries_dir / f"{expected_hash}.json"
    md_path = silver_summaries_dir / f"{expected_hash}.md"

    assert json_path.exists()
    assert md_path.exists()
    assert json_path.stem == md_path.stem
    assert len(json_path.stem) == 64

    with json_path.open() as f:
        json_data = json.load(f)

    assert json_data["status"] == "success"
    assert json_data["summary"] == summary_data["summary"]
    assert "created_at" in json_data
    assert "updated_at" in json_data
    assert "lineage" in json_data

    md_content = md_path.read_text()
    assert "Success" in md_content
    assert summary_data["url"] in md_content
    assert summary_data["summary"] in md_content


@pytest.mark.integration
def test_integration_silver_directory_structure():
    silver_dir = Path("artifacts/silver")
    extracted_content_dir = silver_dir / "extracted_content"
    summaries_dir = silver_dir / "summaries"

    assert silver_dir.exists()
    assert extracted_content_dir.exists()
    assert summaries_dir.exists()


@pytest.mark.integration
def test_markdown_and_json_files_created_for_success():
    import hashlib

    from dagster import OutputContext

    silver_io_manager = SilverIOManager()

    test_url = "https://example.com/markdown-test-success"
    summary_data = {
        "url": test_url,
        "title": "Test Article Title",
        "status": "success",
        "summary": "Summary content here",
        "model": "openai/gpt-4o",
        "tokens_used": 150,
        "latency_ms": 1200,
        "lineage": {
            "source_asset": "silver_extracted_content",
            "source_hash": hashlib.sha256(test_url.encode()).hexdigest(),
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

    summaries_dir = Path("artifacts/silver/summaries")
    expected_hash = hashlib.sha256(test_url.encode()).hexdigest()

    json_path = summaries_dir / f"{expected_hash}.json"
    md_path = summaries_dir / f"{expected_hash}.md"

    assert json_path.exists()
    assert md_path.exists()
    assert len(json_path.stem) == 64
    assert len(md_path.stem) == 64
    assert json_path.stem == md_path.stem


@pytest.mark.integration
def test_markdown_file_created_for_failed_summary():
    import hashlib

    from dagster import OutputContext

    silver_io_manager = SilverIOManager()

    test_url = "https://example.com/markdown-test-failure"
    summary_data = {
        "url": test_url,
        "title": "Failed Article",
        "status": "failed",
        "summary": None,
        "model": None,
        "tokens_used": None,
        "latency_ms": None,
        "error": "Connection timeout",
        "error_type": "TimeoutError",
        "lineage": {
            "source_asset": "silver_extracted_content",
            "source_hash": hashlib.sha256(test_url.encode()).hexdigest(),
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

    summaries_dir = Path("artifacts/silver/summaries")
    expected_hash = hashlib.sha256(test_url.encode()).hexdigest()

    md_path = summaries_dir / f"{expected_hash}.md"
    assert md_path.exists()

    md_content = md_path.read_text()
    assert "Failed" in md_content
    assert test_url in md_content
    assert "Connection timeout" in md_content
    assert "TimeoutError" in md_content


@pytest.mark.integration
def test_markdown_content_structure_success():
    import hashlib

    from dagster import OutputContext

    silver_io_manager = SilverIOManager()

    test_url = "https://example.com/markdown-structure-test"
    test_title = "Comprehensive Test Article"
    summary_data = {
        "url": test_url,
        "title": test_title,
        "status": "success",
        "summary": "- Point 1\n- Point 2\n- Point 3",
        "model": "openai/gpt-4o",
        "tokens_used": 250,
        "latency_ms": 1800,
        "lineage": {
            "source_asset": "silver_extracted_content",
            "source_hash": hashlib.sha256(test_url.encode()).hexdigest(),
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

    summaries_dir = Path("artifacts/silver/summaries")
    expected_hash = hashlib.sha256(test_url.encode()).hexdigest()
    md_path = summaries_dir / f"{expected_hash}.md"

    md_content = md_path.read_text()

    assert f"# {test_title}" in md_content
    assert f"**URL:** {test_url}" in md_content
    assert "**Status:** Success" in md_content
    assert "**Model:** openai/gpt-4o" in md_content
    assert "## Summary" in md_content
    assert "- Point 1" in md_content
    assert "**Tokens:** 250" in md_content
    assert "**Latency:** 1800ms" in md_content
    assert "**Generated:**" in md_content


@pytest.mark.integration
def test_markdown_content_structure_failure():
    import hashlib

    from dagster import OutputContext

    silver_io_manager = SilverIOManager()

    test_url = "https://example.com/markdown-failure-structure"
    summary_data = {
        "url": test_url,
        "title": "Error Test Article",
        "status": "failed",
        "summary": None,
        "model": None,
        "tokens_used": None,
        "latency_ms": None,
        "error": "API rate limit exceeded",
        "error_type": "RateLimitError",
        "lineage": {
            "source_asset": "silver_extracted_content",
            "source_hash": hashlib.sha256(test_url.encode()).hexdigest(),
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

    summaries_dir = Path("artifacts/silver/summaries")
    expected_hash = hashlib.sha256(test_url.encode()).hexdigest()
    md_path = summaries_dir / f"{expected_hash}.md"

    md_content = md_path.read_text()

    assert "# Error Test Article" in md_content
    assert f"**URL:** {test_url}" in md_content
    assert "**Status:** Failed" in md_content
    assert "## Error" in md_content
    assert "API rate limit exceeded" in md_content
    assert "**Error Type:** RateLimitError" in md_content
    assert "**Generated:**" in md_content


@pytest.mark.integration
def test_hash_length_and_matching():
    import hashlib

    from dagster import OutputContext

    silver_io_manager = SilverIOManager()

    test_url = "https://example.com/hash-validation-test"
    summary_data = {
        "url": test_url,
        "title": "Hash Test",
        "status": "success",
        "summary": "Testing hash validation",
        "model": "openai/gpt-4o",
        "tokens_used": 100,
        "latency_ms": 900,
        "lineage": {
            "source_asset": "silver_extracted_content",
            "source_hash": hashlib.sha256(test_url.encode()).hexdigest(),
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

    summaries_dir = Path("artifacts/silver/summaries")
    expected_hash = hashlib.sha256(test_url.encode()).hexdigest()

    json_path = summaries_dir / f"{expected_hash}.json"
    md_path = summaries_dir / f"{expected_hash}.md"

    assert len(expected_hash) == 64
    assert len(json_path.stem) == 64
    assert len(md_path.stem) == 64
    assert json_path.stem == md_path.stem == expected_hash


@pytest.mark.integration
def test_markdown_readability_basic_checks():
    import hashlib

    from dagster import OutputContext

    silver_io_manager = SilverIOManager()

    test_url = "https://example.com/readability-test"
    summary_data = {
        "url": test_url,
        "title": "Readability Test Article",
        "status": "success",
        "summary": "This is a readable summary with proper formatting.",
        "model": "openai/gpt-4o",
        "tokens_used": 120,
        "latency_ms": 1000,
        "lineage": {
            "source_asset": "silver_extracted_content",
            "source_hash": hashlib.sha256(test_url.encode()).hexdigest(),
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

    summaries_dir = Path("artifacts/silver/summaries")
    expected_hash = hashlib.sha256(test_url.encode()).hexdigest()
    md_path = summaries_dir / f"{expected_hash}.md"

    md_content = md_path.read_text()

    assert md_content.startswith("# ")
    assert "**" in md_content
    assert "---" in md_content
    assert "##" in md_content
    assert "\n\n" in md_content

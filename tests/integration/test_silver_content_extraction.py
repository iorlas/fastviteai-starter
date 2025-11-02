import hashlib
import json
from unittest.mock import Mock, patch

import pytest
from dagster import OutputContext, build_asset_context

from dagster_project.assets.silver_extracted_content import silver_extracted_content
from dagster_project.resources.io_managers import SilverIOManager


@pytest.fixture
def silver_test_env(tmp_path, monkeypatch):
    silver_dir = tmp_path / "artifacts" / "silver"
    extracted_content_dir = silver_dir / "extracted_content"
    extracted_content_dir.mkdir(parents=True, exist_ok=True)

    # Set PROJECT_ROOT environment variable
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))

    return {
        "project_root": tmp_path,
        "silver_dir": silver_dir,
        "extracted_content_dir": extracted_content_dir,
    }


@pytest.mark.integration
def test_end_to_end_bronze_to_silver_html_flow(silver_test_env):
    test_html = """
    <html>
        <head><title>Test Article</title></head>
        <body>
            <article>
                <h1>Test Article</h1>
                <p>This is test content.</p>
                <p>Second paragraph.</p>
            </article>
        </body>
    </html>
    """

    test_url = "https://example.com/article"
    bronze_data = [
        {
            "url": test_url,
            "html_content": test_html,
            "download_info": {
                "status_code": 200,
                "headers": {"content-type": "text/html"},
                "download_timestamp": "2025-11-02T00:00:00Z",
            },
        }
    ]

    context = build_asset_context()
    results = silver_extracted_content(context, bronze_data)

    assert len(results) == 1
    assert results[0]["url"] == test_url
    assert results[0]["type"] == "html"
    assert results[0]["title"] == "Test Article"
    assert "test content" in results[0]["content"].lower()
    assert results[0]["metadata"]["extraction_method"] == "beautifulsoup"
    assert "lineage" in results[0]
    assert results[0]["lineage"]["source_asset"] == "bronze_raw_html"

    silver_io_manager = SilverIOManager()

    output_context = OutputContext(
        name="silver_extracted_content",
        step_key="silver_extracted_content",
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

    for result in results:
        silver_io_manager.handle_output(output_context, result)

    url_hash = hashlib.sha256(test_url.encode()).hexdigest()
    expected_file = silver_test_env["extracted_content_dir"] / f"{url_hash}.json"

    assert expected_file.exists()
    assert len(url_hash) == 64

    with expected_file.open() as f:
        saved_data = json.load(f)

    assert saved_data["url"] == test_url
    assert saved_data["type"] == "html"
    assert saved_data["title"] == "Test Article"
    assert "created_at" in saved_data
    assert "updated_at" in saved_data
    assert saved_data["lineage"]["source_asset"] == "bronze_raw_html"


@pytest.mark.integration
def test_reprocessing_from_bronze_cache_no_http_download(silver_test_env, tmp_path):
    test_html = "<html><body><h1>Cached Content</h1><p>Text</p></body></html>"
    test_url = "https://example.com/cached"

    bronze_data = [
        {
            "url": test_url,
            "html_content": test_html,
            "download_info": {
                "status_code": 200,
                "headers": {},
                "download_timestamp": "2025-11-02T00:00:00Z",
            },
        }
    ]

    with patch("httpx.get") as mock_get:
        mock_get.return_value = Mock(text="should not be called", status_code=200)

        context = build_asset_context()
        results = silver_extracted_content(context, bronze_data)

        assert mock_get.call_count == 0, (
            "httpx.get should not be called when extracting from bronze cache"
        )

        assert len(results) == 1
        assert results[0]["url"] == test_url
        assert results[0]["title"] == "Cached Content"


@pytest.mark.integration
def test_metadata_structure_validation(silver_test_env):
    test_html = """
    <html>
        <head>
            <title>Article</title>
            <meta name="author" content="John Doe"/>
            <meta property="article:published_time" content="2025-11-01"/>
        </head>
        <body><article><p>Content</p></article></body>
    </html>
    """

    test_url = "https://example.com/metadata-test"
    bronze_data = [
        {
            "url": test_url,
            "html_content": test_html,
            "download_info": {
                "status_code": 200,
                "headers": {},
                "download_timestamp": "2025-11-02T00:00:00Z",
            },
        }
    ]

    context = build_asset_context()
    results = silver_extracted_content(context, bronze_data)

    assert len(results) == 1
    extracted = results[0]

    assert "url" in extracted
    assert "type" in extracted
    assert extracted["type"] == "html"
    assert "title" in extracted
    assert "content" in extracted
    assert "metadata" in extracted

    metadata = extracted["metadata"]
    assert "author" in metadata
    assert "published_date" in metadata
    assert "word_count" in metadata
    assert "extraction_method" in metadata
    assert metadata["extraction_method"] == "beautifulsoup"

    assert "lineage" in extracted
    lineage = extracted["lineage"]
    assert "source_asset" in lineage
    assert lineage["source_asset"] == "bronze_raw_html"
    assert "source_hash" in lineage
    assert "transformation_timestamp" in lineage
    assert len(lineage["source_hash"]) == 64


@pytest.mark.integration
def test_youtube_extraction_continues_to_work(silver_test_env):
    test_url = "https://youtube.com/watch?v=test123"
    bronze_data = [
        {
            "url": test_url,
            "html_content": "",
            "download_info": {
                "status_code": 200,
                "headers": {},
                "download_timestamp": "2025-11-02T00:00:00Z",
            },
        }
    ]

    mock_yt_content = Mock()
    mock_yt_content.title = "Test Video"
    mock_yt_content.transcript = "Video transcript content"
    mock_yt_content.channel = "Test Channel"
    mock_yt_content.duration = 120
    mock_yt_content.description = "Test description"

    with patch(
        "dagster_project.assets.silver_extracted_content.extract_youtube_content",
        return_value=mock_yt_content,
    ):
        context = build_asset_context()
        results = silver_extracted_content(context, bronze_data)

        assert len(results) == 1
        assert results[0]["url"] == test_url
        assert results[0]["type"] == "youtube"
        assert results[0]["title"] == "Test Video"
        assert results[0]["content"] == "Video transcript content"
        assert results[0]["metadata"]["extraction_method"] == "yt-dlp"
        assert results[0]["metadata"]["channel"] == "Test Channel"


@pytest.mark.integration
def test_error_handling_from_bronze_layer(silver_test_env):
    test_urls = [
        {
            "url": "https://example.com/error",
            "html_content": "",
            "download_info": {
                "status_code": 404,
                "headers": {},
                "download_timestamp": "2025-11-02T00:00:00Z",
                "error": "404 Not Found",
                "error_type": "HTTPStatusError",
            },
        },
        {
            "url": "https://example.com/success",
            "html_content": "<html><body><h1>Success</h1></body></html>",
            "download_info": {
                "status_code": 200,
                "headers": {},
                "download_timestamp": "2025-11-02T00:00:00Z",
            },
        },
    ]

    context = build_asset_context()
    results = silver_extracted_content(context, test_urls)

    assert len(results) == 1
    assert results[0]["url"] == "https://example.com/success"
    assert results[0]["title"] == "Success"


@pytest.mark.integration
def test_full_sha256_hash_filenames(silver_test_env):
    test_html = "<html><body><p>Content</p></body></html>"
    test_url = "https://example.com/hash-test"

    bronze_data = [
        {
            "url": test_url,
            "html_content": test_html,
            "download_info": {
                "status_code": 200,
                "headers": {},
                "download_timestamp": "2025-11-02T00:00:00Z",
            },
        }
    ]

    context = build_asset_context()
    results = silver_extracted_content(context, bronze_data)

    silver_io_manager = SilverIOManager()

    output_context = OutputContext(
        name="silver_extracted_content",
        step_key="silver_extracted_content",
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

    for result in results:
        silver_io_manager.handle_output(output_context, result)

    json_files = list(silver_test_env["extracted_content_dir"].glob("*.json"))
    assert len(json_files) == 1

    filename = json_files[0].stem
    assert len(filename) == 64


@pytest.mark.integration
def test_empty_html_content_handling(silver_test_env):
    bronze_data = [
        {
            "url": "https://example.com/empty",
            "html_content": "",
            "download_info": {
                "status_code": 200,
                "headers": {},
                "download_timestamp": "2025-11-02T00:00:00Z",
            },
        }
    ]

    context = build_asset_context()
    results = silver_extracted_content(context, bronze_data)

    assert len(results) == 0

import hashlib
import json
from unittest.mock import Mock, patch

import httpx
import pytest
from dagster import build_asset_context

from dagster_project.assets.bronze_raw_html import bronze_raw_html
from dagster_project.resources.io_managers import BronzeIOManager


@pytest.fixture
def bronze_html_test_env(tmp_path):
    """Create test environment with bronze directories."""
    bronze_dir = tmp_path / "artifacts" / "bronze"
    raw_html_dir = bronze_dir / "raw_html"
    raw_html_dir.mkdir(parents=True, exist_ok=True)

    return {
        "project_root": tmp_path,
        "bronze_dir": bronze_dir,
        "raw_html_dir": raw_html_dir,
    }


@pytest.mark.integration
def test_bronze_raw_html_download_and_storage(bronze_html_test_env, monkeypatch):
    """Test HTML download and bronze storage via IOManager."""
    # Mock httpx.get to return test HTML
    mock_response = Mock()
    mock_response.text = "<html><body>Test content</body></html>"
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html"}
    mock_response.url = "https://example.com/test"

    with patch("httpx.get", return_value=mock_response):
        # Create BronzeIOManager
        bronze_io_manager = BronzeIOManager(base_dir=str(bronze_html_test_env["bronze_dir"]))

        # Create context
        context = build_asset_context()

        # Execute asset with test URLs
        test_urls = ["https://example.com/test"]
        results = bronze_raw_html(context, test_urls)

        # Verify results
        assert len(results) == 1
        assert results[0]["url"] == "https://example.com/test"
        assert results[0]["html_content"] == "<html><body>Test content</body></html>"
        assert results[0]["download_info"]["status_code"] == 200

        # Simulate IOManager saving
        from dagster import OutputContext

        output_context = OutputContext(
            name="bronze_raw_html",
            step_key="bronze_raw_html",
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
            bronze_io_manager.handle_output(output_context, result)

        # Verify file created with full SHA256 hash
        url_hash = hashlib.sha256(test_urls[0].encode()).hexdigest()
        expected_file = bronze_html_test_env["raw_html_dir"] / f"{url_hash}.json"

        assert expected_file.exists()
        assert len(url_hash) == 64  # Full hash, not truncated


@pytest.mark.integration
def test_bronze_raw_html_cache_hit_behavior(bronze_html_test_env):
    """Test cache hit behavior - second run skips download."""
    from unittest.mock import PropertyMock

    # Create a cached file
    test_url = "https://example.com/cached"
    url_hash = hashlib.sha256(test_url.encode()).hexdigest()
    cached_file = bronze_html_test_env["raw_html_dir"] / f"{url_hash}.json"

    cached_data = {
        "url": test_url,
        "content": "<html>Cached</html>",
        "created_at": "2025-11-01T00:00:00Z",
    }
    with cached_file.open("w") as f:
        json.dump(cached_data, f)

    # Verify file exists
    assert cached_file.exists(), f"Cached file should exist at {cached_file}"

    # Mock httpx.get - should NOT be called for cached URL
    with patch("httpx.get") as mock_get:
        mock_response = Mock()
        mock_response.text = "should not be called"
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.url = test_url
        mock_get.return_value = mock_response

        context = build_asset_context()
        type(context.op_execution_context).op_config = PropertyMock(
            return_value={"project_root": str(bronze_html_test_env["project_root"])}
        )

        results = bronze_raw_html(context, [test_url])

        # Verify httpx.get was NOT called (cache hit)
        assert mock_get.call_count == 0, (
            f"httpx.get should not be called for cached URLs, "
            f"but was called {mock_get.call_count} times"
        )

        # Verify results are empty (cache hits are skipped)
        assert len(results) == 0


@pytest.mark.integration
def test_bronze_raw_html_full_hash_filenames(bronze_html_test_env):
    """Verify all files use 64-char SHA256 hash."""
    from unittest.mock import PropertyMock

    mock_response = Mock()
    mock_response.text = "<html>Test</html>"
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.url = "https://example.com/hash-test"

    with patch("httpx.get", return_value=mock_response):
        bronze_io_manager = BronzeIOManager(base_dir=str(bronze_html_test_env["bronze_dir"]))
        context = build_asset_context()
        type(context.op_execution_context).op_config = PropertyMock(
            return_value={"project_root": str(bronze_html_test_env["project_root"])}
        )

        test_urls = ["https://example.com/hash-test"]
        results = bronze_raw_html(context, test_urls)

        # Save via IOManager
        from dagster import OutputContext

        output_context = OutputContext(
            name="bronze_raw_html",
            step_key="bronze_raw_html",
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
            bronze_io_manager.handle_output(output_context, result)

        # Verify filename uses full 64-char hash
        json_files = list(bronze_html_test_env["raw_html_dir"].glob("*.json"))
        assert len(json_files) == 1

        filename = json_files[0].stem
        assert len(filename) == 64  # Full SHA256, not truncated [:16]


@pytest.mark.integration
def test_bronze_raw_html_metadata_structure(bronze_html_test_env):
    """Test metadata structure in saved JSON."""
    from unittest.mock import PropertyMock

    mock_response = Mock()
    mock_response.text = "<html><body>Content</body></html>"
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html", "server": "test"}
    mock_response.url = "https://example.com/metadata-test"

    with patch("httpx.get", return_value=mock_response):
        bronze_io_manager = BronzeIOManager(base_dir=str(bronze_html_test_env["bronze_dir"]))
        context = build_asset_context()
        type(context.op_execution_context).op_config = PropertyMock(
            return_value={"project_root": str(bronze_html_test_env["project_root"])}
        )

        test_urls = ["https://example.com/metadata-test"]
        results = bronze_raw_html(context, test_urls)

        # Save via IOManager
        from dagster import OutputContext

        output_context = OutputContext(
            name="bronze_raw_html",
            step_key="bronze_raw_html",
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
            bronze_io_manager.handle_output(output_context, result)

        # Load and verify metadata structure
        json_files = list(bronze_html_test_env["raw_html_dir"].glob("*.json"))
        with json_files[0].open() as f:
            data = json.load(f)

        # Verify required fields
        assert "url" in data
        assert "content" in data
        assert "created_at" in data
        assert "download_info" in data

        # Verify download_info has status_code, headers, download_timestamp
        download_info = data["download_info"]
        assert "status_code" in download_info
        assert "headers" in download_info
        assert "download_timestamp" in download_info


@pytest.mark.integration
def test_bronze_raw_html_http_error_handling(bronze_html_test_env):
    """Test HTTP error handling and error metadata storage."""
    from unittest.mock import PropertyMock

    # Mock httpx.get to raise HTTP error
    with patch(
        "httpx.get",
        side_effect=httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=Mock(status_code=404)
        ),
    ):
        context = build_asset_context()
        type(context.op_execution_context).op_config = PropertyMock(
            return_value={"project_root": str(bronze_html_test_env["project_root"])}
        )

        test_urls = ["https://example.com/error-test"]
        results = bronze_raw_html(context, test_urls)

        # Verify asset continues processing and returns error metadata
        assert len(results) == 1
        assert results[0]["url"] == "https://example.com/error-test"
        assert results[0]["html_content"] == ""  # Empty for errors
        assert "error" in results[0]["download_info"]
        assert results[0]["download_info"]["error_type"] == "HTTPStatusError"


@pytest.mark.integration
def test_bronze_raw_html_timeout_handling(bronze_html_test_env):
    """Test timeout handling."""
    from unittest.mock import PropertyMock

    # Mock httpx.get to raise timeout
    with patch("httpx.get", side_effect=httpx.TimeoutException("Request timeout")):
        context = build_asset_context()
        type(context.op_execution_context).op_config = PropertyMock(
            return_value={"project_root": str(bronze_html_test_env["project_root"])}
        )

        test_urls = ["https://example.com/timeout-test"]
        results = bronze_raw_html(context, test_urls)

        # Verify graceful error handling
        assert len(results) == 1
        assert results[0]["url"] == "https://example.com/timeout-test"
        assert "error" in results[0]["download_info"]
        assert results[0]["download_info"]["error_type"] == "TimeoutException"


@pytest.mark.integration
def test_bronze_raw_html_multiple_urls_with_errors(bronze_html_test_env):
    """Test processing continues after errors."""
    from unittest.mock import PropertyMock

    # Mock httpx.get to fail for first URL, succeed for second
    def mock_get_side_effect(url, **kwargs):
        if "fail" in url:
            raise httpx.HTTPError("Failed")
        mock_response = Mock()
        mock_response.text = f"<html>Content for {url}</html>"
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.url = url
        return mock_response

    with patch("httpx.get", side_effect=mock_get_side_effect):
        context = build_asset_context()
        type(context.op_execution_context).op_config = PropertyMock(
            return_value={"project_root": str(bronze_html_test_env["project_root"])}
        )

        test_urls = [
            "https://example.com/fail-test",
            "https://example.com/success-test",
        ]
        results = bronze_raw_html(context, test_urls)

        # Verify both URLs processed (no early exit)
        assert len(results) == 2

        # First URL has error
        assert results[0]["url"] == "https://example.com/fail-test"
        assert "error" in results[0]["download_info"]

        # Second URL succeeded
        assert results[1]["url"] == "https://example.com/success-test"
        assert "<html>Content for" in results[1]["html_content"]

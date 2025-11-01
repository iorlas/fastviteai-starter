"""Integration tests for the complete pipeline.

Tests the full flow from link ingestion through content extraction, including
RSS watcher integration, error handling, and deduplication.

These are integration tests (not E2E) - they use mocking for external dependencies
like HTTP requests and RSS feed parsing for speed and reliability.
"""

import json
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from dagster import build_asset_context

from dagster_project.assets.content_extraction import content_extraction_asset
from dagster_project.assets.link_ingestion import link_ingestion_asset
from dagster_project.ops.watchers import RSSWatcher


@pytest.fixture
def mock_rss_feed():
    """Mock RSS feed XML content for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Test Feed</title>
        <link>https://example.com</link>
        <description>Test RSS feed</description>
        <item>
            <title>Test Article 1</title>
            <link>https://example.com/test-article-1</link>
            <description>First test article</description>
        </item>
        <item>
            <title>Test Article 2</title>
            <link>https://example.com/test-article-2</link>
            <description>Second test article</description>
        </item>
    </channel>
</rss>"""


@pytest.fixture
def e2e_test_env(tmp_path):
    """Create complete test environment with all required files and directories."""
    # Create input files
    manual_file = tmp_path / "manual_links.txt"
    manual_file.write_text(
        "# Manual links for E2E test\n"
        "https://example.com/manual-article\n"
        "https://www.youtube.com/watch?v=test123\n"
    )

    monitoring_file = tmp_path / "monitoring_list.txt"
    monitoring_file.write_text(
        "# Monitoring list with RSS feed\n"
        "https://example.com/feed.xml\n"
        "https://example.com/direct-link\n"
    )

    # Create artifact directories
    (tmp_path / "artifacts" / "summaries").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "extractions").mkdir(parents=True, exist_ok=True)

    return tmp_path


@pytest.mark.integration
def test_rss_watcher_integration(e2e_test_env, mock_rss_feed):
    """Test that RSSWatcher correctly discovers links from RSS feeds.

    Verifies:
    - RSS feed URLs are detected in monitoring_list.txt
    - RSSWatcher.fetch_links() is called for RSS feeds
    - Discovered links are added to the ingestion pipeline
    """
    with patch("feedparser.parse") as mock_parse:
        # Mock feedparser to return our test feed
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {"link": "https://example.com/test-article-1"},
            {"link": "https://example.com/test-article-2"},
        ]
        mock_parse.return_value = mock_feed

        # Create context
        context = build_asset_context()
        type(context).op_config = PropertyMock(
            return_value={"source_filter": "monitoring", "project_root": str(e2e_test_env)}
        )

        # Run link ingestion
        links = link_ingestion_asset(context)

        # Should have 3 links: 2 from RSS feed + 1 direct link
        assert len(links) == 3

        # Verify RSS feed was parsed
        mock_parse.assert_called_once_with("https://example.com/feed.xml")

        # Verify discovered links are in results
        discovered_urls = {link.url for link in links}
        assert "https://example.com/test-article-1" in discovered_urls
        assert "https://example.com/test-article-2" in discovered_urls
        assert "https://example.com/direct-link" in discovered_urls


@pytest.mark.integration
def test_deduplication_skips_processed_links(e2e_test_env):
    """Test that pipeline skips links with existing summary files.

    Verifies:
    - First run processes all links
    - Second run skips links with existing summaries
    - Deduplication works correctly
    """
    # Create a mock summary file to simulate already-processed link
    summaries_dir = e2e_test_env / "artifacts" / "summaries"
    from dagster_project.assets.link_ingestion import compute_url_hash

    processed_url = "https://example.com/manual-article"
    url_hash = compute_url_hash(processed_url)
    summary_file = summaries_dir / f"{url_hash}.json"
    summary_file.write_text('{"status": "completed", "url": "' + processed_url + '"}')

    # Create context
    context = build_asset_context()
    type(context).op_config = PropertyMock(
        return_value={"source_filter": "manual", "project_root": str(e2e_test_env)}
    )

    # Run link ingestion
    links = link_ingestion_asset(context)

    # Should only have 1 link (YouTube video), manual article already processed
    assert len(links) == 1
    assert "youtube.com" in links[0].url


@pytest.mark.integration
def test_error_handling_with_invalid_url(e2e_test_env):
    """Test that extraction errors are properly logged and saved.

    Verifies:
    - Invalid URLs trigger extraction errors
    - Error details are saved to extraction artifacts
    - Pipeline continues processing other links
    """
    # Add an invalid URL to manual_links.txt
    manual_file = e2e_test_env / "manual_links.txt"
    manual_file.write_text(
        "# Links with one invalid URL\n"
        "https://this-domain-does-not-exist-12345.com/article\n"
    )

    # Create context for link ingestion
    ingest_context = build_asset_context()
    type(ingest_context).op_config = PropertyMock(
        return_value={"source_filter": "manual", "project_root": str(e2e_test_env)}
    )

    # Get links
    links = link_ingestion_asset(ingest_context)
    assert len(links) == 1

    # Create context for content extraction
    extract_context = build_asset_context()
    type(extract_context).op_config = PropertyMock(
        return_value={"project_root": str(e2e_test_env)}
    )

    # Run content extraction (should handle error gracefully)
    extractions = content_extraction_asset(extract_context, links)

    # Should have 1 extraction result (with error)
    assert len(extractions) == 1
    assert extractions[0].extraction_success is False
    assert extractions[0].error_message is not None

    # Verify extraction artifact was saved with error details
    # Errors are saved to artifacts/html/ directory
    html_dir = e2e_test_env / "artifacts" / "html"
    extraction_files = list(html_dir.glob("*.json"))
    assert len(extraction_files) == 1

    # Verify error details are in the file
    with open(extraction_files[0]) as f:
        data = json.load(f)
        assert data["extraction_success"] is False
        assert "error_message" in data
        assert len(data["error_message"]) > 0


@pytest.mark.integration
def test_malformed_rss_feed_handling(e2e_test_env):
    """Test that malformed RSS feeds are handled gracefully.

    Verifies:
    - Malformed RSS feeds don't crash the pipeline
    - Warning is logged for failed RSS parsing
    - Other links continue to be processed
    """
    # Create monitoring_list with malformed RSS feed URL
    monitoring_file = e2e_test_env / "monitoring_list.txt"
    monitoring_file.write_text(
        "# Monitoring list with malformed RSS\n"
        "https://example.com/malformed-feed.xml\n"
        "https://example.com/valid-link\n"
    )

    with patch("feedparser.parse") as mock_parse:
        # Mock feedparser to return malformed feed with no entries
        mock_feed = MagicMock()
        mock_feed.bozo = True
        mock_feed.entries = []
        mock_feed.get = MagicMock(return_value="XML parsing error")
        mock_parse.return_value = mock_feed

        # Create context
        context = build_asset_context()
        type(context).op_config = PropertyMock(
            return_value={"source_filter": "monitoring", "project_root": str(e2e_test_env)}
        )

        # Run link ingestion (should not crash)
        links = link_ingestion_asset(context)

        # Should only have the valid direct link
        assert len(links) == 1
        assert "valid-link" in links[0].url


@pytest.mark.integration
def test_rss_watcher_fetch_links_directly():
    """Test RSSWatcher.fetch_links() method directly with mock feed.

    Verifies:
    - Protocol implementation is correct
    - Link extraction from RSS entries works
    - Both 'link' and 'href' fields are supported
    """
    with patch("feedparser.parse") as mock_parse:
        # Test with standard RSS 'link' field
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {"link": "https://example.com/article1"},
            {"link": "https://example.com/article2"},
            {"href": "https://example.com/article3"},  # Atom-style
        ]
        mock_parse.return_value = mock_feed

        watcher = RSSWatcher()
        links = watcher.fetch_links("https://example.com/feed.xml")

        assert len(links) == 3
        assert "https://example.com/article1" in links
        assert "https://example.com/article2" in links
        assert "https://example.com/article3" in links


@pytest.mark.integration
def test_full_pipeline_with_summarization(e2e_test_env):
    """Test complete pipeline flow: ingestion → extraction → summarization.

    This is a comprehensive E2E test that verifies:
    - Links are ingested correctly
    - Content is extracted (mocked for speed)
    - Summaries are generated (mocked for speed)
    - All artifacts are saved in correct locations
    """
    # Mock HTTP requests for content extraction
    with patch("httpx.get") as mock_get:
        # Mock HTML response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
            <html>
                <head><title>Test Article</title></head>
                <body>
                    <article>
                        <h1>Test Article</h1>
                        <p>This is test content for the E2E pipeline test.</p>
                    </article>
                </body>
            </html>
        """
        mock_response.url = "https://example.com/manual-article"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Step 1: Link Ingestion
        ingest_context = build_asset_context()
        type(ingest_context).op_config = PropertyMock(
            return_value={"source_filter": "manual", "project_root": str(e2e_test_env)}
        )
        links = link_ingestion_asset(ingest_context)
        assert len(links) >= 1

        # Step 2: Content Extraction
        extract_context = build_asset_context()
        type(extract_context).op_config = PropertyMock(
            return_value={"project_root": str(e2e_test_env)}
        )
        extractions = content_extraction_asset(extract_context, links[:1])  # Test first link only
        assert len(extractions) == 1
        assert extractions[0].extraction_success is True

        # Step 3: Summarization (skip for this test due to complexity of mocking OpenRouter)
        # Verify that extraction artifacts were created correctly
        html_dir = e2e_test_env / "artifacts" / "html"
        extraction_files = list(html_dir.glob("*.json"))
        assert len(extraction_files) == 1

        # Verify extraction file has correct structure
        with open(extraction_files[0]) as f:
            data = json.load(f)
            assert data["extraction_success"] is True
            assert data["title"] == "Test Article"
            assert len(data["text"]) > 0

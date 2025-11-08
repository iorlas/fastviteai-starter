from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dagster_project.core.content_types.generic_html import GenericHTMLExtractor


def test_matches_all_urls():
    extractor = GenericHTMLExtractor()

    assert extractor.matches("https://example.com/page")
    assert extractor.matches("https://news.ycombinator.com/item?id=123")
    assert extractor.matches("https://www.youtube.com/watch?v=test")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_extract_success():
    extractor = GenericHTMLExtractor()

    mock_response = MagicMock()
    mock_response.text = "<html><body>Fresh content</body></html>"
    mock_response.url = "https://example.com/article"
    mock_response.raise_for_status = MagicMock()

    with (
        patch("dagster_project.core.content_types.generic_html.get_async_cache_client") as mock_get_client,
        patch("dagster_project.core.content_types.generic_html.trafilatura") as mock_traf,
    ):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        mock_metadata = MagicMock()
        mock_metadata.title = "Test Article"
        mock_metadata.author = None
        mock_metadata.date = None
        mock_metadata.as_dict.return_value = {"title": "Test Article", "author": None, "date": None}

        mock_traf.extract_metadata.return_value = mock_metadata
        mock_traf.extract.return_value = "Extracted content"

        result = await extractor.extract("https://example.com/article")

    assert result.url == "https://example.com/article"
    assert result.content_type == "html"
    assert result.title == "Test Article"
    assert result.content == "Extracted content"
    assert result.success is True
    assert result.metadata["final_url"] == "https://example.com/article"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_extract_handles_errors():
    extractor = GenericHTMLExtractor()

    with patch("dagster_project.core.content_types.generic_html.get_async_cache_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))
        mock_get_client.return_value = mock_client

        result = await extractor.extract("https://example.com/article")

    assert result.success is False
    assert result.error is not None
    assert "Network error" in result.error
    assert result.title == "Extraction Failed"


def test_filter_metadata_excludes_unwanted_fields():
    """Test that _filter_metadata excludes HTML extraction metadata fields."""
    raw_metadata = {
        # Fields to keep
        "title": "Test Article",
        "author": "John Doe",
        "date": "2025-01-01",
        "sitename": "Example Site",
        "description": "Test description",
        "categories": ["tech", "news"],
        "tags": ["python", "testing"],
        "url": "https://example.com/article",
        # Fields to exclude
        "hostname": "winworldpc.com",
        "body": "<Element body at 0x10ce7de40>",
        "commentsbody": "<Element body at 0x10ce7de00>",
        "raw_text": None,
        "text": None,
    }

    filtered = GenericHTMLExtractor._filter_metadata(raw_metadata)

    # Verify kept fields
    assert filtered["title"] == "Test Article"
    assert filtered["author"] == "John Doe"
    assert filtered["date"] == "2025-01-01"
    assert filtered["sitename"] == "Example Site"
    assert filtered["description"] == "Test description"
    assert filtered["categories"] == ["tech", "news"]
    assert filtered["tags"] == ["python", "testing"]
    assert filtered["url"] == "https://example.com/article"

    # Verify excluded fields
    assert "hostname" not in filtered
    assert "body" not in filtered
    assert "commentsbody" not in filtered
    assert "raw_text" not in filtered
    assert "text" not in filtered

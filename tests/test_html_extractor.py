from unittest.mock import MagicMock, patch

import pytest

from dagster_project.ops.html_extractor import (
    HTMLContent,
    HTMLExtractionError,
    extract_html_content,
)


@pytest.fixture
def sample_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Article Title</title>
        <meta name="author" content="Test Author">
        <meta property="article:published_time" content="2024-01-01">
    </head>
    <body>
        <script>console.log('test');</script>
        <article>
            <h1>Test Article Title</h1>
            <p>This is the first paragraph.</p>
            <p>This is the second paragraph.</p>
        </article>
        <footer>Footer content</footer>
    </body>
    </html>
    """


@pytest.fixture
def mock_httpx_response(sample_html):
    mock_response = MagicMock()
    mock_response.text = sample_html
    mock_response.url = "https://example.com/article"
    mock_response.raise_for_status = MagicMock()
    return mock_response


def test_extract_html_content_success(mock_httpx_response):
    with patch("dagster_project.ops.html_extractor.httpx.get", return_value=mock_httpx_response):
        result = extract_html_content("https://example.com/article")

    assert isinstance(result, HTMLContent)
    assert result.url == "https://example.com/article"
    assert result.title == "Test Article Title"
    assert "first paragraph" in result.content
    assert "second paragraph" in result.content
    assert result.author == "Test Author"
    assert result.publish_date == "2024-01-01"


def test_extract_html_content_cleans_unwanted_elements(mock_httpx_response):
    with patch("dagster_project.ops.html_extractor.httpx.get", return_value=mock_httpx_response):
        result = extract_html_content("https://example.com/article")

    # Script content should be removed
    assert "console.log" not in result.content
    # Footer should be removed
    assert "Footer content" not in result.content


def test_extract_html_content_http_error():
    with patch("dagster_project.ops.html_extractor.httpx.get") as mock_get:
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(HTMLExtractionError):
            extract_html_content("https://example.com/article")


def test_extract_html_content_metadata():
    html = """
    <html>
    <head><title>Test</title></head>
    <body><p>Content</p></body>
    </html>
    """
    mock_response = MagicMock()
    mock_response.text = html
    mock_response.url = "https://example.com/test"
    mock_response.raise_for_status = MagicMock()

    with patch("dagster_project.ops.html_extractor.httpx.get", return_value=mock_response):
        result = extract_html_content("https://example.com/test")

    assert "content_length" in result.metadata
    assert "extracted_at" in result.metadata
    assert "final_url" in result.metadata

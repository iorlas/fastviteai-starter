from unittest.mock import Mock, patch

import pytest

from dagster_project.core.content_types.youtube import YouTubeExtractor


@pytest.fixture
def mock_youtube_info():
    return {
        "id": "test_video_id",
        "title": "Test Video Title",
        "description": "Test video description.",
        "channel": "Test Channel",
        "uploader": "Test Uploader",
        "duration": 300,
        "upload_date": "20240101",
        "view_count": 1000,
        "like_count": 50,
    }


def test_matches_youtube_urls():
    extractor = YouTubeExtractor()

    assert extractor.matches("https://www.youtube.com/watch?v=test")
    assert extractor.matches("https://youtube.com/watch?v=test")
    assert extractor.matches("https://youtu.be/test")
    assert extractor.matches("https://m.youtube.com/watch?v=test")


def test_does_not_match_non_youtube_urls():
    extractor = YouTubeExtractor()

    assert not extractor.matches("https://example.com/page")
    assert not extractor.matches("https://vimeo.com/123456")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_extract_success(mock_youtube_info):
    extractor = YouTubeExtractor()

    with (
        patch.object(extractor, "_fetch_video_info", return_value=mock_youtube_info),
        patch.object(extractor, "_extract_transcript", return_value="Test transcript"),
    ):
        result = await extractor.extract("https://www.youtube.com/watch?v=test")

    assert result.url == "https://www.youtube.com/watch?v=test"
    assert result.content_type == "youtube"
    assert result.title == "Test Video Title"
    assert result.content == "Test transcript"
    assert result.success is True
    assert result.content_metadata["channel"] == "Test Channel"
    assert result.content_metadata["duration"] == 300


@pytest.mark.asyncio
@pytest.mark.integration
async def test_extract_no_transcript(mock_youtube_info):
    extractor = YouTubeExtractor()

    with (
        patch.object(extractor, "_fetch_video_info", return_value=mock_youtube_info),
        patch.object(extractor, "_extract_transcript", return_value=None),
    ):
        result = await extractor.extract("https://www.youtube.com/watch?v=test")

    assert result.success is False
    assert result.error is not None
    assert "No transcript available" in result.error
    assert result.title == "Extraction Failed"


def test_format_transcript():
    """Test short video (<1 hour) with minute-based grouping."""
    mock_entry_1 = Mock()
    mock_entry_1.text = "Hello world"
    mock_entry_1.start = 0.0
    mock_entry_2 = Mock()
    mock_entry_2.text = "This is a test"
    mock_entry_2.start = 5.5
    mock_entry_3 = Mock()
    mock_entry_3.text = "transcript"
    mock_entry_3.start = 125.0

    transcript_data = [mock_entry_1, mock_entry_2, mock_entry_3]

    result = YouTubeExtractor._format_transcript(transcript_data)

    expected = "[0m]\nHello world This is a test\n[2m]\ntranscript"
    assert result == expected


def test_format_transcript_long_video():
    """Test long video (>= 1 hour) with hour:minute format."""
    mock_entry_1 = Mock()
    mock_entry_1.text = "Introduction"
    mock_entry_1.start = 0.0
    mock_entry_2 = Mock()
    mock_entry_2.text = "First topic"
    mock_entry_2.start = 65.0  # 1 minute 5 seconds
    mock_entry_3 = Mock()
    mock_entry_3.text = "Advanced concepts"
    mock_entry_3.start = 3700.0  # 1 hour 1 minute 40 seconds
    mock_entry_4 = Mock()
    mock_entry_4.text = "More details"
    mock_entry_4.start = 3750.0  # 1 hour 2 minutes 30 seconds

    transcript_data = [mock_entry_1, mock_entry_2, mock_entry_3, mock_entry_4]

    result = YouTubeExtractor._format_transcript(transcript_data)

    expected = "[0h00m]\nIntroduction\n[0h01m]\nFirst topic\n[1h01m]\nAdvanced concepts\n[1h02m]\nMore details"
    assert result == expected


def test_format_transcript_empty():
    result = YouTubeExtractor._format_transcript([])
    assert result == ""

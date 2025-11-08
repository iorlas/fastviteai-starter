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


def test_filter_metadata_excludes_format_fields():
    """Test that _filter_metadata excludes video format and codec fields."""
    raw_info = {
        # Fields to keep
        "id": "test_video_id",
        "title": "Test Video",
        "description": "Test description",
        "channel": "Test Channel",
        "uploader": "Test Uploader",
        "duration": 300,
        "upload_date": "20240101",
        "view_count": 1000,
        "like_count": 50,
        "release_year": 2025,
        # Fields to exclude - large/verbose
        "thumbnails": [{"url": "thumb1.jpg"}, {"url": "thumb2.jpg"}],
        "formats": [{"format_id": "399", "ext": "webm"}],
        "_format_sort_fields": ["quality", "res"],
        "automatic_captions": {"en": []},
        "requested_subtitles": {"en": {}},
        "requested_formats": [{"format_id": "399+251"}],
        "subtitles": {"en": []},
        # Fields to exclude - codec/format details
        "vcodec": "av01.0.08M.08",
        "acodec": "opus",
        "resolution": "1920x1080",
        "format": "399 - 1920x1080 (1080p)+251 - audio only (medium)",
        "format_id": "399+251",
        "format_note": "1080p+medium",
        "ext": "webm",
        "protocol": "https+https",
        # Fields to exclude - technical stream details
        "tbr": 304.763,
        "vbr": 173.17,
        "abr": 131.593,
        "fps": 30,
        "width": 1920,
        "height": 1080,
        "dynamic_range": "SDR",
        "stretched_ratio": None,
        "aspect_ratio": 1.78,
        "asr": 48000,
        "audio_channels": 2,
        "filesize_approx": 14461370,
    }

    filtered = YouTubeExtractor._filter_metadata(raw_info)

    # Verify kept fields
    assert filtered["id"] == "test_video_id"
    assert filtered["title"] == "Test Video"
    assert filtered["description"] == "Test description"
    assert filtered["channel"] == "Test Channel"
    assert filtered["duration"] == 300
    assert filtered["upload_date"] == "20240101"
    assert filtered["view_count"] == 1000
    assert filtered["release_year"] == 2025

    # Verify excluded fields
    assert "thumbnails" not in filtered
    assert "formats" not in filtered
    assert "_format_sort_fields" not in filtered
    assert "automatic_captions" not in filtered
    assert "requested_subtitles" not in filtered
    assert "requested_formats" not in filtered
    assert "subtitles" not in filtered
    assert "vcodec" not in filtered
    assert "acodec" not in filtered
    assert "resolution" not in filtered
    assert "format" not in filtered
    assert "format_id" not in filtered
    assert "format_note" not in filtered
    assert "ext" not in filtered
    assert "protocol" not in filtered
    assert "tbr" not in filtered
    assert "vbr" not in filtered
    assert "abr" not in filtered
    assert "fps" not in filtered
    assert "width" not in filtered
    assert "height" not in filtered
    assert "dynamic_range" not in filtered
    assert "stretched_ratio" not in filtered
    assert "aspect_ratio" not in filtered
    assert "asr" not in filtered
    assert "audio_channels" not in filtered
    assert "filesize_approx" not in filtered

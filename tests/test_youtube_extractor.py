from unittest.mock import MagicMock, patch

import pytest
from yt_dlp.utils import DownloadError

from dagster_project.ops.youtube_extractor import (
    YouTubeContent,
    YouTubeExtractionError,
    extract_youtube_content,
)


@pytest.fixture
def mock_youtube_info():
    return {
        "id": "test_video_id",
        "title": "Test Video Title",
        "description": "Test video description with useful information.",
        "channel": "Test Channel",
        "uploader": "Test Uploader",
        "duration": 300,
        "upload_date": "20240101",
        "view_count": 1000,
        "like_count": 50,
    }


def test_extract_youtube_content_success(mock_youtube_info):
    with patch("dagster_project.ops.youtube_extractor.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_youtube_info
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        result = extract_youtube_content("https://www.youtube.com/watch?v=test")

    assert isinstance(result, YouTubeContent)
    assert result.url == "https://www.youtube.com/watch?v=test"
    assert result.title == "Test Video Title"
    assert result.description == "Test video description with useful information."
    assert result.channel == "Test Channel"
    assert result.duration == 300


def test_extract_youtube_content_fallback_to_description(mock_youtube_info):
    # Remove transcript-related fields
    mock_youtube_info.pop("automatic_captions", None)
    mock_youtube_info.pop("subtitles", None)

    with patch("dagster_project.ops.youtube_extractor.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_youtube_info
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        result = extract_youtube_content("https://www.youtube.com/watch?v=test")

    # Transcript should fall back to description
    assert result.transcript == "Test video description with useful information."


def test_extract_youtube_content_private_video():
    with patch("dagster_project.ops.youtube_extractor.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        # Simulate DownloadError with "private" message
        mock_ydl.extract_info.side_effect = DownloadError("Video is private")
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        with pytest.raises(YouTubeExtractionError) as exc_info:
            extract_youtube_content("https://www.youtube.com/watch?v=private")

        assert "private" in str(exc_info.value).lower()


def test_extract_youtube_content_metadata(mock_youtube_info):
    with patch("dagster_project.ops.youtube_extractor.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_youtube_info
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl_class.return_value = mock_ydl

        result = extract_youtube_content("https://www.youtube.com/watch?v=test")

    assert "video_id" in result.metadata
    assert "upload_date" in result.metadata
    assert "view_count" in result.metadata
    assert "extracted_at" in result.metadata
    assert result.metadata["video_id"] == "test_video_id"

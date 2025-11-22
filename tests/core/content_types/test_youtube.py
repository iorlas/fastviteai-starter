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


@pytest.fixture
def mock_storage(tmp_path):
    storage = Mock()
    storage.get_path = Mock(return_value=tmp_path / "bronze" / "youtube_downloads" / "test_video_id" / "metadata.json")
    return storage


def test_matches_youtube_urls():
    assert YouTubeExtractor.matches("https://www.youtube.com/watch?v=test")
    assert YouTubeExtractor.matches("https://youtube.com/watch?v=test")
    assert YouTubeExtractor.matches("https://youtu.be/test")
    assert YouTubeExtractor.matches("https://m.youtube.com/watch?v=test")


def test_does_not_match_non_youtube_urls():
    assert not YouTubeExtractor.matches("https://example.com/page")
    assert not YouTubeExtractor.matches("https://vimeo.com/123456")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_download_video_success(mock_youtube_info, tmp_path):
    """Test download_video() creates VideoDownloadResult with correct metadata"""
    extractor = YouTubeExtractor()
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()

    with (
        patch.object(extractor, "_fetch_video_info", return_value=mock_youtube_info),
        patch.object(extractor, "_download_audio") as mock_download,
    ):
        result = await extractor.download_video("https://www.youtube.com/watch?v=test", download_dir)

    assert result.url == "https://www.youtube.com/watch?v=test"
    assert result.video_id == "test"
    assert result.title == "Test Video Title"
    assert result.success is True
    assert result.content_metadata["channel"] == "Test Channel"
    assert result.content_metadata["duration"] == 300
    assert result.created_at is not None
    mock_download.assert_called_once()


# NOTE: Transcription tests moved to tests/assets/test_bronze_youtube_transcription.py
# The transcription logic was moved from YouTubeExtractor to the asset layer

# NOTE: Transcription caching tests moved to tests/core/tools/transcriber/
# The _transcribe_with_whisper method was moved to Transcriber class
# @pytest.mark.asyncio
# async def test_transcription_caching(mock_storage, tmp_path):
#     """Test that transcription results are cached and reused"""
#     # TODO: Move this test to test_transcriber.py


# @pytest.mark.asyncio
# async def test_transcription_cache_miss_and_save(mock_storage, tmp_path):
#     """Test that transcription results are saved to cache on cache miss"""
#     # TODO: Move this test to test_transcriber.py


# @pytest.mark.asyncio
# async def test_progress_callback_invoked_during_transcription(mock_storage, tmp_path):
#     """Test that progress_callback is invoked during Whisper transcription with correct parameters"""
#     # TODO: Move this test to test_transcriber.py


# def test_format_transcript():
#     """Test transcript formatting"""
#     # TODO: Move this test to test_transcriber.py (test Transcriber._format_llm_optimized)


# def test_format_transcript_long_video():
#     """Test transcript formatting for long videos"""
#     # TODO: Move this test to test_transcriber.py


# def test_format_transcript_empty():
#     """Test transcript formatting with empty segments"""
#     # TODO: Move this test to test_transcriber.py


def test_filter_metadata_excludes_format_fields():
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


def test_extractor_proxy_configuration():
    proxy_url = "http://proxy.example.com:8080"
    extractor = YouTubeExtractor(proxy=proxy_url)

    assert extractor.proxy == proxy_url


def test_extractor_no_proxy_by_default():
    extractor = YouTubeExtractor()

    assert extractor.proxy is None


@pytest.mark.asyncio
async def test_proxy_passed_to_yt_dlp(mock_youtube_info):
    proxy_url = "http://proxy.example.com:8080"
    extractor = YouTubeExtractor(proxy=proxy_url)

    with patch("yt_dlp.YoutubeDL") as mock_ydl:
        mock_instance = Mock()
        mock_instance.__enter__ = Mock(return_value=mock_instance)
        mock_instance.__exit__ = Mock(return_value=False)
        mock_instance.extract_info = Mock(return_value=mock_youtube_info)
        mock_ydl.return_value = mock_instance

        # Call _fetch_video_info which should configure yt_dlp with proxy
        extractor._fetch_video_info("https://www.youtube.com/watch?v=test")

        # Verify yt_dlp was called with proxy in options
        call_args = mock_ydl.call_args
        ydl_opts = call_args[0][0]
        assert ydl_opts["proxy"] == proxy_url


# OLD TRANSCRIPT API TEST - Commented out for potential revert
# @pytest.mark.asyncio
# async def test_proxy_passed_to_transcript_api(mock_youtube_info):
#     proxy_url = "http://proxy.example.com:8080"
#     extractor = YouTubeExtractor(proxy=proxy_url)
#
#     with (
#         patch("dagster_project.core.content_types.youtube.Session") as mock_session_class,
#         patch("dagster_project.core.content_types.youtube.YouTubeTranscriptApi") as mock_api_class,
#     ):
#         mock_session = Mock()
#         mock_session_class.return_value = mock_session
#
#         mock_api = Mock()
#         mock_api_class.return_value = mock_api
#
#         # Mock transcript list
#         mock_transcript_list = Mock()
#         mock_transcript = Mock()
#         mock_transcript.fetch = Mock(return_value=[])
#         mock_transcript_list.find_manually_created_transcript = Mock(return_value=mock_transcript)
#         mock_api.list = Mock(return_value=mock_transcript_list)
#
#         # Call _extract_transcript
#         extractor._extract_transcript(mock_youtube_info)
#
#         # Verify Session was created and proxy was set
#         mock_session_class.assert_called_once()
#         assert mock_session.proxies == {"http": proxy_url, "https": proxy_url}
#
#         # Verify YouTubeTranscriptApi was called with the session
#         mock_api_class.assert_called_once_with(http_client=mock_session)

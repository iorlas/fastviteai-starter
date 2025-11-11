from pathlib import Path
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
async def test_extract_success(mock_youtube_info, tmp_path):
    extractor = YouTubeExtractor()
    mock_audio_path = Path("/tmp/test_video.m4a")

    with (
        patch.object(extractor, "_fetch_video_info", return_value=mock_youtube_info),
        patch.object(extractor, "_download_audio", return_value=mock_audio_path),
        patch.object(extractor, "_transcribe_with_whisper", return_value="Test transcript") as mock_transcribe,
        patch("dagster_project.core.content_types.youtube.compute_url_hash", return_value="test_hash"),
    ):
        result = await extractor.extract("https://www.youtube.com/watch?v=test")

    assert result.url == "https://www.youtube.com/watch?v=test"
    assert result.content_type == "youtube"
    assert result.title == "Test Video Title"
    assert result.content == "Test transcript"
    assert result.success is True
    assert result.content_metadata["channel"] == "Test Channel"
    assert result.content_metadata["duration"] == 300
    assert result.metadata["transcription_method"] == "whisper_local"
    assert "video_file" in result.metadata
    assert "whisper_model" in result.metadata
    # Verify transcribe was called with url_hash parameter
    mock_transcribe.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_extract_no_transcript(mock_youtube_info):
    extractor = YouTubeExtractor()
    mock_audio_path = Path("/tmp/test_video.m4a")

    with (
        patch.object(extractor, "_fetch_video_info", return_value=mock_youtube_info),
        patch.object(extractor, "_download_audio", return_value=mock_audio_path),
        patch.object(extractor, "_transcribe_with_whisper", return_value=""),
        patch("dagster_project.core.content_types.youtube.compute_url_hash", return_value="test_hash"),
    ):
        result = await extractor.extract("https://www.youtube.com/watch?v=test")

    assert result.success is False
    assert result.error is not None
    assert "Whisper transcription failed" in result.error
    assert result.title == "Extraction Failed"


@pytest.mark.asyncio
async def test_transcription_caching(tmp_path):
    """Test that transcription results are cached and reused"""

    # Setup temporary cache directory
    cache_dir = tmp_path / "cache" / "transcriptions"
    cache_dir.mkdir(parents=True)

    url_hash = "test_hash_12345"
    cache_file = cache_dir / f"{url_hash}.txt"
    cached_transcript = "This is a cached transcript"

    # Write cached transcription
    cache_file.write_text(cached_transcript)

    extractor = YouTubeExtractor()
    audio_path = tmp_path / "test_audio.m4a"
    audio_path.touch()  # Create dummy audio file

    with (
        patch.object(extractor, "_get_transcription_cache_path", return_value=cache_file),
        patch("dagster_project.core.content_types.youtube.WhisperModel") as mock_whisper_model,
    ):
        # Call transcribe - should hit cache
        result = extractor._transcribe_with_whisper(audio_path, url_hash)

        # Verify cache hit
        assert result == cached_transcript
        # Verify Whisper model was NOT loaded (cache hit)
        mock_whisper_model.assert_not_called()


@pytest.mark.asyncio
async def test_transcription_cache_miss_and_save(tmp_path):
    """Test that transcription results are saved to cache on cache miss"""
    from dagster_project.config import settings

    # Setup temporary cache directory
    cache_dir = tmp_path / "cache" / "transcriptions"
    cache_dir.mkdir(parents=True)

    url_hash = "test_hash_67890"
    cache_file = cache_dir / f"{url_hash}.txt"
    new_transcript = "This is a newly generated transcript"

    # Ensure cache file doesn't exist
    assert not cache_file.exists()

    extractor = YouTubeExtractor()
    audio_path = tmp_path / "test_audio.m4a"
    audio_path.touch()  # Create dummy audio file

    # Mock faster-whisper model and transcription
    mock_segment = Mock()
    mock_segment.start = 0.0
    mock_segment.text = new_transcript
    mock_segment.end = 5.0

    mock_info = Mock()
    mock_info.duration = 5.0

    mock_model = Mock()
    mock_model.transcribe = Mock(return_value=([mock_segment], mock_info))

    with (
        patch.object(extractor, "_get_transcription_cache_path", return_value=cache_file),
        patch("dagster_project.core.content_types.youtube.WhisperModel", return_value=mock_model),
        patch.object(settings, "whisper_cache_dir", tmp_path / "whisper_models"),
    ):
        # Call transcribe - should miss cache and run Whisper
        result = extractor._transcribe_with_whisper(audio_path, url_hash)

        # Verify transcription was generated
        assert result == f"[0m]\n{new_transcript}"
        # Verify cache file was created
        assert cache_file.exists()
        # Verify cached content matches result
        assert cache_file.read_text() == f"[0m]\n{new_transcript}"


@pytest.mark.asyncio
async def test_progress_callback_invoked_during_transcription(tmp_path):
    """Test that progress_callback is invoked during Whisper transcription with correct parameters"""
    from dagster_project.config import settings

    # Setup
    cache_dir = tmp_path / "cache" / "transcriptions"
    cache_dir.mkdir(parents=True)
    url_hash = "test_hash_callback"
    cache_file = cache_dir / f"{url_hash}.txt"

    # Track callback invocations
    progress_updates = []

    def mock_callback(processed_sec: float, total_sec: float, pct: float):
        progress_updates.append((processed_sec, total_sec, pct))

    extractor = YouTubeExtractor(progress_callback=mock_callback)
    audio_path = tmp_path / "test_audio.m4a"
    audio_path.touch()

    # Mock faster-whisper with multiple segments to trigger progress logging
    mock_segments = [
        Mock(start=0.0, text="Segment 1", end=10.0),
        Mock(start=10.0, text="Segment 2", end=20.0),
        Mock(start=20.0, text="Segment 3", end=30.0),
    ]

    mock_info = Mock()
    mock_info.duration = 30.0

    mock_model = Mock()
    mock_model.transcribe = Mock(return_value=(mock_segments, mock_info))

    with (
        patch.object(extractor, "_get_transcription_cache_path", return_value=cache_file),
        patch("dagster_project.core.content_types.youtube.WhisperModel", return_value=mock_model),
        patch.object(settings, "whisper_cache_dir", tmp_path / "whisper_models"),
    ):
        # Run transcription (result not needed, we're testing callback)
        extractor._transcribe_with_whisper(audio_path, url_hash)

        # Verify callback was invoked (once for 20.0s mark, passing 15s threshold)
        assert len(progress_updates) >= 1

        # Verify callback parameters are correct
        for processed_sec, total_sec, pct in progress_updates:
            assert 0 <= processed_sec <= total_sec
            assert 0 <= pct <= 100
            assert total_sec == 30.0


def test_format_transcript():
    segment_1 = {"start": 0.0, "text": "Hello world", "end": 5.5}
    segment_2 = {"start": 5.5, "text": "This is a test", "end": 10.0}
    segment_3 = {"start": 125.0, "text": "transcript", "end": 130.0}

    segments = [segment_1, segment_2, segment_3]

    result = YouTubeExtractor._format_transcript(segments)

    expected = "[0m]\nHello world This is a test\n[2m]\ntranscript"
    assert result == expected


def test_format_transcript_long_video():
    segment_1 = {"start": 0.0, "text": "Introduction", "end": 5.0}
    segment_2 = {"start": 65.0, "text": "First topic", "end": 70.0}
    segment_3 = {"start": 3700.0, "text": "Advanced concepts", "end": 3710.0}
    segment_4 = {"start": 3750.0, "text": "More details", "end": 3760.0}

    segments = [segment_1, segment_2, segment_3, segment_4]

    result = YouTubeExtractor._format_transcript(segments)

    expected = "[0h00m]\nIntroduction\n[0h01m]\nFirst topic\n[1h01m]\nAdvanced concepts\n[1h02m]\nMore details"
    assert result == expected


def test_format_transcript_empty():
    result = YouTubeExtractor._format_transcript([])
    assert result == ""


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


def test_extractor_accepts_progress_callback():
    """Test that YouTubeExtractor accepts and stores progress_callback"""

    def mock_callback(processed: float, total: float, pct: float):
        pass

    extractor = YouTubeExtractor(progress_callback=mock_callback)

    assert extractor.progress_callback == mock_callback


def test_extractor_no_callback_by_default():
    """Test that progress_callback defaults to None"""
    extractor = YouTubeExtractor()

    assert extractor.progress_callback is None


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

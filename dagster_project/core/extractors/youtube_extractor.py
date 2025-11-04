from datetime import UTC, datetime
from typing import Any, NamedTuple

import yt_dlp
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)
from yt_dlp.utils import DownloadError


class YouTubeContent(NamedTuple):
    url: str
    title: str
    transcript: str
    description: str
    channel: str
    duration: int | None
    metadata: dict


class YouTubeExtractionError(Exception):
    pass


def extract_youtube_content(url: str) -> YouTubeContent:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en"],
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video information
            info = ydl.extract_info(url, download=False)

            if not info:
                raise YouTubeExtractionError(f"Failed to extract info from {url}")

            # Extract basic metadata
            title = info.get("title", "Untitled")
            description = info.get("description", "")
            channel = info.get("channel", info.get("uploader", "Unknown"))
            duration = info.get("duration")

            # Try to get transcript
            transcript = _extract_transcript(info)

            # If no transcript available, fail the extraction
            if transcript is None:
                raise YouTubeExtractionError(f"No transcript available for video: {url}")

            # Build metadata dict
            extracted_at = datetime.now(UTC).isoformat()
            metadata = {
                "video_id": info.get("id", ""),
                "upload_date": info.get("upload_date", ""),
                "view_count": info.get("view_count", 0),
                "like_count": info.get("like_count", 0),
                "extracted_at": extracted_at,
                "has_transcript": True,
            }

            return YouTubeContent(
                url=url,
                title=title,
                transcript=transcript,
                description=description,
                channel=channel,
                duration=duration,
                metadata=metadata,
            )

    except DownloadError as e:
        # Handle private/unavailable videos
        error_msg = str(e).lower()
        if "private" in error_msg or "unavailable" in error_msg:
            raise YouTubeExtractionError(f"Video is private or unavailable: {url}") from e
        raise YouTubeExtractionError(f"yt-dlp error for {url}: {e}") from e
    except Exception as e:
        raise YouTubeExtractionError(f"Error extracting content from {url}: {e}") from e


def _extract_transcript(info: dict) -> str | None:
    """Extract transcript with fallback logic:
    1. Manual English transcript
    2. Manual transcript in original language
    3. Auto-generated English transcript
    4. Auto-generated transcript in original language
    Returns None if no transcript available.
    """
    video_id = info.get("id")
    if not video_id:
        return None

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        # 1. Try manual English first (preferred)
        try:
            transcript = transcript_list.find_manually_created_transcript(["en", "en-US", "en-GB"])
            return _format_transcript(transcript.fetch())
        except NoTranscriptFound:
            pass

        # 2. Try any manual transcript (original language)
        for transcript in transcript_list:
            if not transcript.is_generated:
                return _format_transcript(transcript.fetch())

        # 3. Try auto-generated English
        try:
            transcript = transcript_list.find_generated_transcript(["en", "en-US", "en-GB"])
            return _format_transcript(transcript.fetch())
        except NoTranscriptFound:
            pass

        # 4. Try any auto-generated transcript
        for transcript in transcript_list:
            if transcript.is_generated:
                return _format_transcript(transcript.fetch())

        return None

    except (NoTranscriptFound, TranscriptsDisabled):
        return None
    except Exception:
        return None


def _format_transcript(transcript_data: Any) -> str:
    """Format transcript data into plain text.
    Accepts FetchedTranscript or iterable of transcript snippets.
    """
    return " ".join(entry["text"] for entry in transcript_data)

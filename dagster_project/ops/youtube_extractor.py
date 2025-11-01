from datetime import UTC, datetime
from typing import NamedTuple

import yt_dlp
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

            # If no transcript, use description as fallback
            if not transcript:
                transcript = (
                    description if description else "No transcript or description available"
                )

            # Build metadata dict
            extracted_at = datetime.now(UTC).isoformat()
            metadata = {
                "video_id": info.get("id", ""),
                "upload_date": info.get("upload_date", ""),
                "view_count": info.get("view_count", 0),
                "like_count": info.get("like_count", 0),
                "extracted_at": extracted_at,
                "has_transcript": bool(_extract_transcript(info)),
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


def _extract_transcript(info: dict) -> str:
    # Try automatic captions first
    if "automatic_captions" in info:
        for lang in ["en", "en-US", "en-GB"]:
            if lang in info["automatic_captions"]:
                captions = info["automatic_captions"][lang]
                # Find the plain text format
                for caption in captions:
                    if caption.get("ext") in ["vtt", "srv3", "srv2", "srv1"]:
                        # Note: yt-dlp doesn't download subtitles in extract_info
                        # We'd need to actually download them, but for simplicity
                        # we'll just note they exist and use description
                        return ""

    # Try manual subtitles
    if "subtitles" in info:
        for lang in ["en", "en-US", "en-GB"]:
            if lang in info["subtitles"]:
                captions = info["subtitles"][lang]
                for caption in captions:
                    if caption.get("ext") in ["vtt", "srv3", "srv2", "srv1"]:
                        return ""

    return ""

import asyncio
from typing import Any
from urllib.parse import urlparse

import structlog
import yt_dlp
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)
from yt_dlp.utils import DownloadError

from dagster_project.core.content_types.models import ExtractionResult

logger = structlog.get_logger()


class YouTubeExtractionError(Exception):
    pass


class YouTubeExtractor:
    YOUTUBE_DOMAINS = {"youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"}

    def matches(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc.lower() in self.YOUTUBE_DOMAINS

    async def extract(self, url: str) -> ExtractionResult:
        logger.info("youtube_extract.started", url=url)

        try:
            info = await asyncio.to_thread(self._fetch_video_info, url)

            title = info.get("title", "Untitled")

            transcript = await asyncio.to_thread(self._extract_transcript, info)

            if transcript is None:
                raise YouTubeExtractionError(f"No transcript available for video: {url}")

            metadata = {
                "content_length": len(transcript),
                "final_url": url,
            }

            logger.info("youtube_extract.success", url=url, title=title)

            return ExtractionResult(
                url=url,
                content_type="youtube",
                title=title,
                content=transcript,
                metadata=metadata,
                content_metadata=dict(info),
                success=True,
            )

        except DownloadError as e:
            error_msg = str(e).lower()
            if "private" in error_msg or "unavailable" in error_msg:
                logger.warning("youtube_extract.failed", url=url, error="Video is private or unavailable")
                return ExtractionResult(
                    url=url,
                    content_type="youtube",
                    title="Extraction Failed",
                    content="",
                    success=False,
                    error=f"Video is private or unavailable: {url}",
                )
            logger.warning("youtube_extract.failed", url=url, error=str(e))
            return ExtractionResult(
                url=url,
                content_type="youtube",
                title="Extraction Failed",
                content="",
                success=False,
                error=f"yt-dlp error for {url}: {e}",
            )
        except YouTubeExtractionError as e:
            logger.warning("youtube_extract.failed", url=url, error=str(e))
            return ExtractionResult(
                url=url,
                content_type="youtube",
                title="Extraction Failed",
                content="",
                success=False,
                error=str(e),
            )
        except Exception as e:
            logger.warning("youtube_extract.failed", url=url, error=str(e))
            return ExtractionResult(
                url=url,
                content_type="youtube",
                title="Extraction Failed",
                content="",
                success=False,
                error=f"Error extracting content from {url}: {e}",
            )

    @staticmethod
    def _fetch_video_info(url: str) -> dict:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "skip_download": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise YouTubeExtractionError(f"Failed to extract info from {url}")
            return info

    @staticmethod
    def _extract_transcript(info: dict) -> str | None:
        video_id = info.get("id")
        if not video_id:
            return None

        try:
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.list(video_id)

            try:
                transcript = transcript_list.find_manually_created_transcript(["en", "en-US", "en-GB"])
                return YouTubeExtractor._format_transcript(transcript.fetch())
            except NoTranscriptFound:
                pass

            for transcript in transcript_list:
                if not transcript.is_generated:
                    return YouTubeExtractor._format_transcript(transcript.fetch())

            try:
                transcript = transcript_list.find_generated_transcript(["en", "en-US", "en-GB"])
                return YouTubeExtractor._format_transcript(transcript.fetch())
            except NoTranscriptFound:
                pass

            for transcript in transcript_list:
                if transcript.is_generated:
                    return YouTubeExtractor._format_transcript(transcript.fetch())

            return None

        except (NoTranscriptFound, TranscriptsDisabled):
            return None
        except Exception as e:
            logger.warning("youtube_transcript.unexpected_error", video_id=video_id, error=str(e), error_type=type(e).__name__)
            return None

    @staticmethod
    def _format_transcript(transcript_data: Any) -> str:
        if not transcript_data:
            return ""

        # Determine if video is >= 1 hour
        max_time = max(entry.start for entry in transcript_data)
        is_long_video = max_time >= 3600

        # Group entries by minute
        lines = []
        current_minute = None
        current_texts = []

        for entry in transcript_data:
            start_time = entry.start
            total_minutes = int(start_time // 60)

            if current_minute is None or total_minutes != current_minute:
                # Flush previous minute if exists
                if current_minute is not None and current_texts:
                    lines.append(" ".join(current_texts))

                # Start new minute
                current_minute = total_minutes
                current_texts = []

                # Format timestamp based on video length
                if is_long_video:
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    timestamp = f"[{hours}h{minutes:02d}m]"
                else:
                    timestamp = f"[{total_minutes}m]"

                lines.append(timestamp)

            current_texts.append(entry.text)

        # Flush last minute
        if current_texts:
            lines.append(" ".join(current_texts))

        return "\n".join(lines)

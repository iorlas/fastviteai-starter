import asyncio
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import structlog
import yt_dlp
from pydantic import BaseModel

logger = structlog.get_logger()


class YouTubeExtractionError(Exception):
    pass


class VideoDownloadResult(BaseModel):
    url: str
    video_id: str
    title: str
    content_metadata: dict
    created_at: str


class YouTubeExtractor:
    YOUTUBE_DOMAINS = {"youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"}

    def __init__(self, proxy: str | None = None):
        """
        Initialize YouTube content extractor.

        Args:
            proxy: HTTP/SOCKS5 proxy URL for network requests
        """
        self.proxy = proxy

    @staticmethod
    def matches(url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc.lower() in YouTubeExtractor.YOUTUBE_DOMAINS

    @staticmethod
    def extract_video_id(url: str) -> str:
        parsed = urlparse(url)

        if parsed.netloc.lower() == "youtu.be":
            return parsed.path.lstrip("/").split("/")[0].split("?")[0]

        if "youtube.com" in parsed.netloc.lower():
            query_params = parse_qs(parsed.query)
            if "v" in query_params:
                return query_params["v"][0]

        raise YouTubeExtractionError(f"Could not extract video ID from URL: {url}")

    async def download_video(self, url: str, download_dir: Path) -> VideoDownloadResult:
        logger.info("youtube_download.started", url=url)

        video_id = self.extract_video_id(url)

        video_path = download_dir / "video.m4a"

        info = await asyncio.to_thread(self._fetch_video_info, url)
        title = info.get("title", "Untitled")

        await asyncio.to_thread(self._download_audio, url, video_path)

        created_at = datetime.now(UTC).isoformat()

        logger.info("youtube_download.success", url=url, video_id=video_id, title=title)

        return VideoDownloadResult(
            url=url,
            video_id=video_id,
            title=title,
            content_metadata=self._filter_metadata(info),
            created_at=created_at,
        )

    @staticmethod
    def _filter_metadata(info: dict) -> dict:
        excluded_fields = {
            # Large/verbose metadata
            "thumbnails",
            "formats",
            "_format_sort_fields",
            "automatic_captions",
            "requested_subtitles",
            "requested_formats",
            "subtitles",
            # Video/audio codec details
            "vcodec",
            "acodec",
            "resolution",
            # Format-specific fields
            "format",
            "format_id",
            "format_note",
            "ext",
            "protocol",
            # Technical stream details
            "tbr",
            "vbr",
            "abr",
            "fps",
            "width",
            "height",
            "dynamic_range",
            "stretched_ratio",
            "aspect_ratio",
            "asr",
            "audio_channels",
            "filesize_approx",
        }

        return {k: v for k, v in info.items() if k not in excluded_fields}

    def _build_base_ydl_opts(self) -> dict:
        """Build base yt-dlp options with proxy configuration"""
        opts = {
            "quiet": True,
            "no_warnings": True,
        }
        if self.proxy:
            opts["proxy"] = self.proxy
        return opts

    def _download_audio(self, url: str, output_path: Path) -> None:
        """Download audio-only file using yt-dlp"""
        # Skip download if file already exists
        if output_path.exists():
            logger.info("youtube_audio.exists", url=url, path=str(output_path))
            return

        ydl_opts = self._build_base_ydl_opts()
        ydl_opts.update(
            {
                "format": "bestaudio/best",
                "outtmpl": str(output_path.with_suffix("")),  # Remove extension, yt-dlp will add it
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "m4a",
                    }
                ],
            }
        )

        logger.info("youtube_audio.downloading", url=url, path=str(output_path))
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Validate download succeeded
        if not output_path.exists():
            raise YouTubeExtractionError(f"Download failed: file not created at {output_path}")

        file_size = output_path.stat().st_size
        if file_size < 1024:  # Less than 1KB is suspicious
            raise YouTubeExtractionError(f"Download failed: file too small ({file_size} bytes)")

        logger.info("youtube_audio.downloaded", url=url, path=str(output_path), size_mb=round(file_size / 1024 / 1024, 2))

    def _fetch_video_info(self, url: str) -> dict:
        ydl_opts = self._build_base_ydl_opts()
        ydl_opts.update(
            {
                "extract_flat": False,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["en"],
                "skip_download": True,
            }
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise YouTubeExtractionError(f"Failed to extract info from {url}")
            return info

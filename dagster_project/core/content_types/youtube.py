import asyncio
from collections.abc import Callable
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import structlog
import yt_dlp
from faster_whisper import WhisperModel
from pydantic import BaseModel
from yt_dlp.utils import DownloadError

from dagster_project.config import settings
from dagster_project.core.content_types.models import ExtractionResult
from dagster_project.utils.url_utils import compute_url_hash

logger = structlog.get_logger()


class YouTubeExtractionError(Exception):
    pass


class VideoDownloadResult(BaseModel):
    url: str
    video_id: str
    video_path: str
    title: str
    content_metadata: dict
    success: bool
    error: str | None = None
    created_at: str


class YouTubeExtractor:
    YOUTUBE_DOMAINS = {"youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"}

    def __init__(
        self,
        proxy: str | None = None,
        progress_callback: Callable[[float, float, float], None] | None = None,
    ):
        """
        Initialize YouTube content extractor.

        Args:
            proxy: HTTP/SOCKS5 proxy URL for network requests
            progress_callback: Optional callback for Whisper transcription progress updates.
                              Signature: (processed_seconds, total_seconds, progress_pct) -> None
        """
        self.proxy = proxy
        self.progress_callback = progress_callback

    def matches(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc.lower() in self.YOUTUBE_DOMAINS

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

    async def extract(self, url: str) -> ExtractionResult:
        logger.info("youtube_extract.started", url=url)

        try:
            # Get URL hash for storage
            url_hash = compute_url_hash(url)

            # Fetch video metadata
            info = await asyncio.to_thread(self._fetch_video_info, url)
            title = info.get("title", "Untitled")

            # Download audio file
            audio_path = await asyncio.to_thread(self._download_audio, url, url_hash)

            # Transcribe with Whisper
            transcript = await asyncio.to_thread(self._transcribe_with_whisper, audio_path, url_hash)

            if not transcript:
                raise YouTubeExtractionError(f"Whisper transcription failed for video: {url}")

            metadata = {
                "content_length": len(transcript),
                "final_url": url,
                "transcription_method": "whisper_local",
                "video_file": f"{url_hash}.m4a",
                "whisper_model": settings.whisper_model,
            }

            logger.info("youtube_extract.success", url=url, title=title)

            return ExtractionResult(
                url=url,
                content_type="youtube",
                title=title,
                content=transcript,
                metadata=metadata,
                content_metadata=self._filter_metadata(info),
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

    async def download_video(self, url: str) -> VideoDownloadResult:
        logger.info("youtube_download.started", url=url)

        try:
            video_id = self.extract_video_id(url)

            download_dir = settings.artifacts_path / "bronze" / "youtube_downloads" / video_id
            video_path = download_dir / "video"
            metadata_path = download_dir / "metadata.json"

            if video_path.exists() and metadata_path.exists():
                logger.info("youtube_download.cache_hit", url=url, video_id=video_id)

                import json
                from datetime import UTC, datetime

                metadata = json.loads(metadata_path.read_text())
                return VideoDownloadResult(
                    url=url,
                    video_id=video_id,
                    video_path=str(video_path.relative_to(settings.artifacts_path / "bronze")),
                    title=metadata.get("title", "Untitled"),
                    content_metadata=metadata.get("content_metadata", {}),
                    success=True,
                    created_at=metadata.get("created_at", datetime.now(UTC).isoformat()),
                )

            download_dir.mkdir(parents=True, exist_ok=True)

            info = await asyncio.to_thread(self._fetch_video_info, url)
            title = info.get("title", "Untitled")

            await asyncio.to_thread(self._download_audio_to_path, url, video_path)

            import json
            from datetime import UTC, datetime

            created_at = datetime.now(UTC).isoformat()
            metadata = {
                "title": title,
                "content_metadata": self._filter_metadata(info),
                "created_at": created_at,
            }

            metadata_path.write_text(json.dumps(metadata, indent=2))

            logger.info("youtube_download.success", url=url, video_id=video_id, title=title)

            return VideoDownloadResult(
                url=url,
                video_id=video_id,
                video_path=str(video_path.relative_to(settings.artifacts_path / "bronze")),
                title=title,
                content_metadata=self._filter_metadata(info),
                success=True,
                created_at=created_at,
            )

        except DownloadError as e:
            error_msg = str(e).lower()
            if "private" in error_msg or "unavailable" in error_msg:
                logger.warning("youtube_download.failed", url=url, error="Video is private or unavailable")
                error_message = f"Video is private or unavailable: {url}"
            else:
                logger.warning("youtube_download.failed", url=url, error=str(e))
                error_message = f"yt-dlp error for {url}: {e}"

            return VideoDownloadResult(
                url=url,
                video_id="",
                video_path="",
                title="Download Failed",
                content_metadata={},
                success=False,
                error=error_message,
                created_at="",
            )
        except Exception as e:
            logger.warning("youtube_download.failed", url=url, error=str(e))
            return VideoDownloadResult(
                url=url,
                video_id="",
                video_path="",
                title="Download Failed",
                content_metadata={},
                success=False,
                error=f"Error downloading video from {url}: {e}",
                created_at="",
            )

    async def transcribe_video(self, video_id: str, url: str, url_hash: str, title: str, content_metadata: dict) -> ExtractionResult:
        logger.info("youtube_transcribe.started", url=url, video_id=video_id)

        try:
            video_path = settings.artifacts_path / "bronze" / "youtube_downloads" / video_id / "video"

            if not video_path.exists():
                raise YouTubeExtractionError(f"Video file not found: {video_path}")

            transcript = await asyncio.to_thread(self._transcribe_with_whisper, video_path, url_hash)

            if not transcript:
                raise YouTubeExtractionError(f"Whisper transcription failed for video: {url}")

            metadata = {
                "content_length": len(transcript),
                "final_url": url,
                "transcription_method": "whisper_local",
                "video_id": video_id,
                "video_file": f"youtube_downloads/{video_id}/video",
                "whisper_model": settings.whisper_model,
            }

            logger.info("youtube_transcribe.success", url=url, video_id=video_id, title=title)

            return ExtractionResult(
                url=url,
                content_type="youtube",
                title=title,
                content=transcript,
                metadata=metadata,
                content_metadata=content_metadata,
                success=True,
            )

        except YouTubeExtractionError as e:
            logger.warning("youtube_transcribe.failed", url=url, error=str(e))
            return ExtractionResult(
                url=url,
                content_type="youtube",
                title="Transcription Failed",
                content="",
                success=False,
                error=str(e),
            )
        except Exception as e:
            logger.warning("youtube_transcribe.failed", url=url, error=str(e))
            return ExtractionResult(
                url=url,
                content_type="youtube",
                title="Transcription Failed",
                content="",
                success=False,
                error=f"Error transcribing video from {url}: {e}",
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

    @staticmethod
    def _get_video_storage_path(url_hash: str) -> Path:
        """Get storage path for video file"""
        videos_dir = settings.artifacts_path / "bronze" / "youtube_videos"
        videos_dir.mkdir(parents=True, exist_ok=True)
        return videos_dir / f"{url_hash}.m4a"

    @staticmethod
    def _get_transcription_cache_path(url_hash: str) -> Path:
        """Get storage path for cached transcription"""
        transcriptions_dir = settings.artifacts_path / "cache" / "transcriptions"
        transcriptions_dir.mkdir(parents=True, exist_ok=True)
        return transcriptions_dir / f"{url_hash}.txt"

    def _download_audio(self, url: str, url_hash: str) -> Path:
        """Download audio-only file using yt-dlp"""
        output_path = self._get_video_storage_path(url_hash)

        # Skip download if file already exists
        if output_path.exists():
            logger.info("youtube_audio.exists", url=url, path=str(output_path))
            return output_path

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(output_path.with_suffix("")),  # Remove extension, yt-dlp will add it
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                }
            ],
        }

        # Add proxy if configured
        if self.proxy:
            ydl_opts["proxy"] = self.proxy

        logger.info("youtube_audio.downloading", url=url, path=str(output_path))
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        logger.info("youtube_audio.downloaded", url=url, path=str(output_path))
        return output_path

    def _download_audio_to_path(self, url: str, output_path: Path) -> None:
        """Download audio-only file to specific path using yt-dlp (no extension)"""
        if output_path.exists():
            logger.info("youtube_audio.exists", url=url, path=str(output_path))
            return

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(output_path),
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                }
            ],
        }

        if self.proxy:
            ydl_opts["proxy"] = self.proxy

        logger.info("youtube_audio.downloading", url=url, path=str(output_path))
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        logger.info("youtube_audio.downloaded", url=url, path=str(output_path))

    def _transcribe_with_whisper(self, audio_path: Path, url_hash: str) -> str:
        """Transcribe audio file using faster-whisper with progress tracking"""
        # Check transcription cache first
        cache_path = self._get_transcription_cache_path(url_hash)

        if cache_path.exists():
            logger.info("whisper.cache_hit", audio_path=str(audio_path), cache_path=str(cache_path))
            return cache_path.read_text()

        # Cache miss - run Whisper transcription
        logger.info("whisper.cache_miss", audio_path=str(audio_path))

        cache_dir = settings.whisper_cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "whisper.loading_model",
            model=settings.whisper_model,
            device=settings.whisper_device,
            cache_dir=str(cache_dir),
        )

        # Initialize faster-whisper model
        model = WhisperModel(
            settings.whisper_model,
            device=settings.whisper_device,
            download_root=str(cache_dir),
            compute_type="int8",  # Optimized inference
        )

        logger.info("whisper.model_loaded", model=settings.whisper_model)
        logger.info("whisper.transcribing", audio_path=str(audio_path))

        # Transcribe with generator pattern for progress tracking
        segments_generator, info = model.transcribe(
            str(audio_path),
            language="en",
            vad_filter=True,  # Voice activity detection
        )

        # Collect segments with progress logging
        segments = []
        total_duration = info.duration if hasattr(info, "duration") else None
        last_progress_log = 0.0

        for segment in segments_generator:
            segments.append(
                {
                    "start": segment.start,
                    "text": segment.text,
                    "end": segment.end,
                }
            )

            # Log progress every 15 seconds of audio
            if total_duration and segment.end - last_progress_log >= 15.0:
                progress_pct = (segment.end / total_duration) * 100

                # Call progress callback if provided (for Dagster UI visibility)
                if self.progress_callback:
                    self.progress_callback(segment.end, total_duration, progress_pct)

                # Keep structlog for debugging (appears in compute logs)
                logger.info(
                    "whisper.progress",
                    audio_path=str(audio_path),
                    processed_seconds=round(segment.end, 1),
                    total_seconds=round(total_duration, 1),
                    progress_pct=round(progress_pct, 1),
                )
                last_progress_log = segment.end

        transcript_text = self._format_transcript(segments)
        logger.info("whisper.transcribed", audio_path=str(audio_path), length=len(transcript_text), segments=len(segments))

        # Save transcription to cache
        cache_path.write_text(transcript_text)
        logger.info("whisper.cached", cache_path=str(cache_path), length=len(transcript_text))

        return transcript_text

    def _fetch_video_info(self, url: str) -> dict:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "skip_download": True,
        }

        # Add proxy if configured
        if self.proxy:
            ydl_opts["proxy"] = self.proxy

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise YouTubeExtractionError(f"Failed to extract info from {url}")
            return info

    # OLD TRANSCRIPT API METHOD - Commented out for potential revert
    # def _extract_transcript(self, info: dict) -> str | None:
    #     video_id = info.get("id")
    #     if not video_id:
    #         return None
    #
    #     try:
    #         # Configure proxy using requests Session (supports HTTP, HTTPS, and SOCKS5)
    #         if self.proxy:
    #             http_client = Session()
    #             http_client.proxies = {
    #                 "http": self.proxy,
    #                 "https": self.proxy,
    #             }
    #             ytt_api = YouTubeTranscriptApi(http_client=http_client)
    #         else:
    #             ytt_api = YouTubeTranscriptApi()
    #
    #         transcript_list = ytt_api.list(video_id)
    #
    #         try:
    #             transcript = transcript_list.find_manually_created_transcript(["en", "en-US", "en-GB"])
    #             return YouTubeExtractor._format_transcript(transcript.fetch())
    #         except NoTranscriptFound:
    #             pass
    #
    #         for transcript in transcript_list:
    #             if not transcript.is_generated:
    #                 return YouTubeExtractor._format_transcript(transcript.fetch())
    #
    #         try:
    #             transcript = transcript_list.find_generated_transcript(["en", "en-US", "en-GB"])
    #             return YouTubeExtractor._format_transcript(transcript.fetch())
    #         except NoTranscriptFound:
    #             pass
    #
    #         for transcript in transcript_list:
    #             if transcript.is_generated:
    #                 return YouTubeExtractor._format_transcript(transcript.fetch())
    #
    #         return None
    #
    #     except (NoTranscriptFound, TranscriptsDisabled):
    #         return None

    @staticmethod
    def _format_transcript(segments: list[dict]) -> str:
        if not segments:
            return ""

        # Determine if video is >= 1 hour
        max_time = max(seg["start"] for seg in segments)
        is_long_video = max_time >= 3600

        # Group entries by minute
        lines = []
        current_minute = None
        current_texts = []

        for segment in segments:
            start_time = segment["start"]
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

            current_texts.append(segment["text"].strip())

        # Flush last minute
        if current_texts:
            lines.append(" ".join(current_texts))

        return "\n".join(lines)

import traceback

import structlog
from dagster import AssetExecutionContext, asset

from dagster_project.config import settings
from dagster_project.core.content_types.youtube import YouTubeExtractionError, YouTubeExtractor
from dagster_project.core.tools.transcriber.transcriber import Transcriber
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.tables import BronzeTable

logger = structlog.get_logger()


@asset(
    deps=["bronze_youtube_download"],
    required_resource_keys={"bronze_storage"},
    compute_kind="python",
    group_name="bronze_layer",
    tags={"layer": "bronze", "source": "youtube_api", "content_type": "youtube", "phase": "transcription"},
)
async def bronze_youtube_transcription(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> None:
    bronze_storage = context.resources.bronze_storage

    def log_whisper_progress(processed_sec: float, total_sec: float, pct: float) -> None:
        context.log.info(f"Whisper transcription progress: {pct:.1f}% ({processed_sec:.0f}/{total_sec:.0f}s)")

    transcriber = Transcriber(
        model=settings.whisper_model,
        device=settings.whisper_device,
        model_cache_dir=settings.whisper_cache_dir,
        progress_callback=log_whisper_progress,
    )

    youtube_urls = [u for u in discovered_urls if u["content_type"] == "youtube"]

    stats = Stats(total=len(youtube_urls))
    context.log.info(f"Processing {stats.total} YouTube videos for transcription")

    for url_data in youtube_urls:
        url = url_data["url"]

        try:
            video_id = YouTubeExtractor.extract_video_id(url)
        except Exception as e:
            context.log.warning(f"✗ Failed to extract video ID: {url} - {e}")
            stats.failed += 1
            continue

        if bronze_storage.exists(BronzeTable.YOUTUBE_DOWNLOADS, "transcription", sub_partition=video_id):
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        # Check if download metadata exists before attempting to load
        if not bronze_storage.exists(BronzeTable.YOUTUBE_DOWNLOADS, "metadata", sub_partition=video_id):
            context.log.warning(f"✗ Download metadata not found for video_id: {video_id}, skipping transcription")
            stats.failed += 1
            continue

        download_data = bronze_storage.load(BronzeTable.YOUTUBE_DOWNLOADS, "metadata", sub_partition=video_id)

        if not download_data:
            context.log.warning(f"✗ Download data not found for video_id: {video_id}")
            stats.failed += 1
            continue

        if not download_data.get("success"):
            error_msg = download_data.get("error", "Unknown error")
            context.log.warning(f"✗ Download failed, skipping transcription: {url} - {error_msg}")
            stats.failed += 1
            continue

        context.log.info(f"Transcribing YouTube video: {url}")

        # Compute download directory and video path
        download_dir = bronze_storage.get_path(BronzeTable.YOUTUBE_DOWNLOADS, "metadata", sub_partition=video_id).parent
        video_path = download_dir / "video.m4a"

        try:
            # Validate video file exists
            if not video_path.exists():
                raise YouTubeExtractionError(f"Video file not found: {video_path}")

            # Transcribe audio
            logger.info("youtube_transcribe.started", url=url, video_id=video_id)
            transcription_result = await transcriber.transcribe(video_path, format="llm_optimized")

            if not transcription_result.text:
                raise YouTubeExtractionError(f"Whisper transcription failed for video: {url}")

            # Construct result metadata
            result = {
                "content": transcription_result.text,
                "metadata": {
                    "content_length": len(transcription_result.text),
                    "final_url": url,
                    "transcription_method": "whisper_local",
                    "video_id": video_id,
                    "whisper_model": settings.whisper_model,
                },
                "created_at": transcription_result.created_at,
            }

            bronze_storage.save(BronzeTable.YOUTUBE_DOWNLOADS, "transcription", result, sub_partition=video_id)

            logger.info("youtube_transcribe.success", url=url, video_id=video_id)
            context.log.info(f"✓ Transcribed: {url}")
            stats.processed += 1
        except Exception:
            context.log.error(f"✗ Exception during transcription: {url}\n{traceback.format_exc()}")
            stats.failed += 1
            continue

    context.log.info(f"YouTube transcription complete: {stats.processed} transcribed, {stats.cached} cached, {stats.failed} failed")
    context.add_output_metadata(stats.model_dump())

from dagster import AssetExecutionContext, asset

from dagster_project.config import settings
from dagster_project.core.content_types.youtube import YouTubeExtractor
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.tables import BronzeTable


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

    extractor = YouTubeExtractor(
        proxy=settings.http_proxy,
        progress_callback=log_whisper_progress,
    )

    youtube_urls = [u for u in discovered_urls if u["content_type"] == "youtube"]

    stats = Stats(total=len(youtube_urls))
    context.log.info(f"Processing {stats.total} YouTube videos for transcription")

    for url_data in youtube_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if bronze_storage.exists(BronzeTable.YOUTUBE, url_hash):
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        try:
            video_id = YouTubeExtractor.extract_video_id(url)
        except Exception as e:
            context.log.warning(f"✗ Failed to extract video ID: {url} - {e}")
            stats.failed += 1
            continue

        download_data = bronze_storage.load(BronzeTable.YOUTUBE_DOWNLOADS, video_id)

        if not download_data:
            context.log.warning(f"✗ Download data not found for video_id: {video_id}")
            stats.failed += 1
            continue

        if not download_data.get("success"):
            context.log.warning(f"✗ Download failed, skipping transcription: {url}")
            stats.failed += 1
            continue

        context.log.info(f"Transcribing YouTube video: {url}")

        result = await extractor.transcribe_video(
            video_id=download_data["video_id"],
            url=url,
            url_hash=url_hash,
            title=download_data["title"],
            content_metadata=download_data["content_metadata"],
        )

        bronze_data = {**result.model_dump(), "url_hash": url_hash}

        bronze_storage.save(BronzeTable.YOUTUBE, url_hash, bronze_data)

        if result.success:
            context.log.info(f"✓ Transcribed: {result.title}")
            stats.processed += 1
        else:
            context.log.warning(f"✗ Transcription failed: {url} - {result.error}")
            stats.failed += 1

    context.log.info(f"YouTube transcription complete: {stats.processed} transcribed, {stats.cached} cached, {stats.failed} failed")
    context.add_output_metadata(stats.model_dump())

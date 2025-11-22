import traceback

from dagster import AssetExecutionContext, asset

from dagster_project.config import settings
from dagster_project.core.content_types.youtube import YouTubeExtractor
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.tables import BronzeTable


@asset(
    required_resource_keys={"bronze_storage"},
    compute_kind="python",
    group_name="bronze_layer",
    tags={"layer": "bronze", "source": "youtube_api", "content_type": "youtube", "phase": "download"},
)
async def bronze_youtube_download(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> None:
    bronze_storage = context.resources.bronze_storage

    extractor = YouTubeExtractor(proxy=settings.http_proxy)

    youtube_urls = [u for u in discovered_urls if u["content_type"] == "youtube"]

    stats = Stats(total=len(youtube_urls))
    context.log.info(f"Processing {stats.total} YouTube URLs for download")

    for url_data in youtube_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        try:
            video_id = YouTubeExtractor.extract_video_id(url)
        except Exception as e:
            context.log.warning(f"✗ Failed to extract video ID: {url} - {e}")
            stats.failed += 1
            continue

        # Check cache at asset level
        if bronze_storage.exists(BronzeTable.YOUTUBE_DOWNLOADS, "metadata", sub_partition=video_id):
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        # Compute download directory
        download_dir = bronze_storage.get_path(BronzeTable.YOUTUBE_DOWNLOADS, "metadata", sub_partition=video_id).parent

        try:
            result = await extractor.download_video(url, download_dir)

            bronze_storage.save(
                BronzeTable.YOUTUBE_DOWNLOADS,
                "metadata",
                result.model_dump(),
                sub_partition=result.video_id if result.video_id else url_hash,
            )

            if result.success:
                context.log.info(f"✓ Downloaded: {result.title} (video_id: {result.video_id})")
                stats.processed += 1
            else:
                context.log.warning(f"✗ Download failed: {url} - {result.error}")
                stats.failed += 1
        except Exception:
            context.log.error(f"✗ Exception during download: {url}\n{traceback.format_exc()}")
            stats.failed += 1
            continue

    context.log.info(f"YouTube download complete: {stats.processed} downloaded, {stats.cached} cached, {stats.failed} failed")
    context.add_output_metadata(stats.model_dump())

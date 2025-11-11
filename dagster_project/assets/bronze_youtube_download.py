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

        result = await extractor.download_video(url)

        download_data = {**result.model_dump(), "url_hash": url_hash}

        bronze_storage.save(BronzeTable.YOUTUBE_DOWNLOADS, result.video_id if result.video_id else url_hash, download_data)

        if result.success:
            context.log.info(f"✓ Downloaded: {result.title} (video_id: {result.video_id})")
            stats.processed += 1
        else:
            context.log.warning(f"✗ Download failed: {url} - {result.error}")
            stats.failed += 1

    context.log.info(f"YouTube download complete: {stats.processed} downloaded, {stats.failed} failed")
    context.add_output_metadata(stats.model_dump())

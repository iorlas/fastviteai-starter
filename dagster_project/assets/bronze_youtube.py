from dagster import AssetExecutionContext, asset

from dagster_project.core.content_types.youtube import YouTubeExtractor
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.tables import BronzeTable


@asset(
    required_resource_keys={"bronze_storage"},
    compute_kind="python",
    group_name="bronze_layer",
    tags={"layer": "bronze", "source": "youtube_api", "content_type": "youtube"},
)
async def bronze_youtube(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> None:
    bronze_storage = context.resources.bronze_storage
    extractor = YouTubeExtractor()

    youtube_urls = [u for u in discovered_urls if u["content_type"] == "youtube"]

    stats = Stats(total=len(youtube_urls))
    context.log.info(f"Processing {stats.total} YouTube URLs in bronze layer")

    for url_data in youtube_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if bronze_storage.exists(BronzeTable.YOUTUBE, url_hash):
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        context.log.info(f"Extracting YouTube content: {url}")

        result = await extractor.extract(url)

        bronze_data = {**result.model_dump(), "url_hash": url_hash}

        bronze_storage.save(BronzeTable.YOUTUBE, url_hash, bronze_data)

        if result.success:
            context.log.info(f"✓ Extracted: {result.title}")
            stats.processed += 1
        else:
            context.log.warning(f"✗ Extraction failed: {url} - {result.error}")
            stats.failed += 1

    context.log.info(f"Bronze YouTube layer complete: {stats.processed} extracted, {stats.cached} cached, {stats.failed} failed")
    context.add_output_metadata(stats.model_dump())

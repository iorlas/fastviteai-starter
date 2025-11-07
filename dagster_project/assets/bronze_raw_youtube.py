from datetime import UTC, datetime

from dagster import AssetExecutionContext, asset

from dagster_project.core.extractors.youtube_extractor import (
    YouTubeExtractionError,
    extract_youtube_content,
)
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.content_type import ContentType
from dagster_project.utils.tables import BronzeTable
from dagster_project.utils.url_utils import extract_aggregator_info


@asset(
    required_resource_keys={"bronze_storage"},
    compute_kind="python",
    group_name="bronze_layer",
    tags={"layer": "bronze", "source": "youtube_api", "content_type": "youtube"},
)
def bronze_raw_youtube(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> None:
    bronze_storage = context.resources.bronze_storage

    youtube_urls = [u for u in discovered_urls if u["content_type"] == ContentType.YOUTUBE.value]

    stats = Stats(total=len(youtube_urls))
    context.log.info(f"Processing {stats.total} YouTube URLs in bronze layer")

    for url_data in youtube_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if bronze_storage.exists(BronzeTable.RAW_YOUTUBE, url_hash):
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        aggregator_info = extract_aggregator_info(url_data)

        context.log.info(f"Extracting YouTube content: {url}")

        try:
            yt_content = extract_youtube_content(url)

            bronze_data = {
                "url": url,
                "url_hash": url_hash,
                "content_type": ContentType.YOUTUBE.value,
                "title": yt_content.title,
                "transcript": yt_content.transcript,
                "description": yt_content.description,
                "channel": yt_content.channel,
                "duration": yt_content.duration,
                "youtube_metadata": yt_content.metadata,
                "aggregator_metadata": {
                    "was_aggregator": bool(aggregator_info),
                    **aggregator_info,
                },
                "extraction_success": True,
                "error_message": None,
                "created_at": datetime.now(UTC).isoformat(),
            }

            bronze_storage.save(BronzeTable.RAW_YOUTUBE, url_hash, bronze_data)

            context.log.info(f"✓ Extracted and stored: {yt_content.title}")
            stats.processed += 1

        except YouTubeExtractionError as e:
            context.log.warning(f"✗ Extraction failed: {url} - {e}")

            bronze_data = {
                "url": url,
                "url_hash": url_hash,
                "content_type": ContentType.YOUTUBE.value,
                "title": "Extraction Failed",
                "transcript": "",
                "description": "",
                "channel": "",
                "duration": None,
                "youtube_metadata": {},
                "aggregator_metadata": {
                    "was_aggregator": bool(aggregator_info),
                    **aggregator_info,
                },
                "extraction_success": False,
                "error_message": str(e),
                "created_at": datetime.now(UTC).isoformat(),
            }

            bronze_storage.save(BronzeTable.RAW_YOUTUBE, url_hash, bronze_data)
            stats.failed += 1

    context.log.info(f"Bronze YouTube layer complete: {stats.processed} extracted, {stats.cached} cached, {stats.failed} failed")
    context.add_output_metadata(stats.model_dump())

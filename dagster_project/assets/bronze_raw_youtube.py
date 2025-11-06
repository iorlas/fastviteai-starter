from datetime import UTC, datetime

from dagster import AssetExecutionContext, asset

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

        context.log.info(f"Storing YouTube metadata: {url}")

        bronze_data = {
            "url": url,
            "url_hash": url_hash,
            "content_type": ContentType.YOUTUBE.value,
            "metadata": {
                "was_aggregator": bool(aggregator_info),
                **aggregator_info,
            },
            "created_at": datetime.now(UTC).isoformat(),
        }

        bronze_storage.save(BronzeTable.RAW_YOUTUBE, url_hash, bronze_data)

        context.log.info(f"✓ Stored: {url}")
        stats.processed += 1

    context.log.info(f"Bronze YouTube layer complete: {stats.processed} stored, {stats.cached} cached")
    context.add_output_metadata(stats.model_dump())

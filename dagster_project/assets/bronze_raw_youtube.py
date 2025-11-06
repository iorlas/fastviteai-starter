import structlog
from dagster import AssetExecutionContext, asset

from dagster_project.utils.content_type import ContentType, detect_content_type

logger = structlog.get_logger()


@asset(
    required_resource_keys={"bronze_io_manager"},
    compute_kind="python",
    group_name="bronze_layer",
    tags={"layer": "bronze", "source": "youtube_api", "content_type": "youtube"},
)
def bronze_raw_youtube(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> dict:
    """Store YouTube URL metadata for discovered YouTube URLs.

    YouTube content doesn't require HTTP download - metadata is stored
    for lineage tracking, actual extraction happens in silver layer.

    Returns summary statistics.
    """
    bronze_io_manager = context.resources.bronze_io_manager

    youtube_urls = [u for u in discovered_urls if detect_content_type(u["url"]) == ContentType.YOUTUBE]

    total_urls = len(youtube_urls)
    context.log.info(f"Processing {total_urls} YouTube URLs in bronze layer")
    processed = 0
    cached = 0

    for url_data in youtube_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if bronze_io_manager.exists("bronze_raw_youtube", url_hash):
            logger.info("bronze.youtube.cache_hit", url_hash=url_hash, url=url)
            cached += 1
            continue

        was_aggregator = url_data.get("was_aggregator", False)
        aggregator_info = {}
        if url_data.get("original_url"):
            aggregator_info = {
                "original_url": url_data.get("original_url"),
                "aggregator_type": url_data.get("aggregator_type"),
                "aggregator_title": url_data.get("aggregator_title"),
            }

        logger.info(
            "bronze.youtube.storing",
            url_hash=url_hash,
            url=url,
            was_aggregator=was_aggregator,
            **aggregator_info,
        )

        bronze_data = {
            "url": url,
            "url_hash": url_hash,
            "content_type": ContentType.YOUTUBE.value,
            "metadata": {
                "was_aggregator": was_aggregator,
                **aggregator_info,
            },
        }

        bronze_io_manager.save("bronze_raw_youtube", url_hash, bronze_data)

        logger.info(
            "bronze.youtube.stored",
            url_hash=url_hash,
            url=url,
            was_aggregator=was_aggregator,
            **aggregator_info,
        )
        processed += 1

    context.log.info(f"Bronze YouTube layer complete: {processed} stored, {cached} cached (total: {total_urls})")
    logger.info(
        "bronze.youtube.complete",
        total=total_urls,
        processed=processed,
        cached=cached,
    )

    context.add_output_metadata(
        {
            "total_urls": total_urls,
            "processed": processed,
            "cached": cached,
        }
    )

    return {
        "total_urls": total_urls,
        "processed": processed,
        "cached": cached,
    }

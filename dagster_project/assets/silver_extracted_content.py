import structlog
from dagster import AssetExecutionContext, asset

from dagster_project.core.content_extractor import ContentExtractor, ExtractionRequest

logger = structlog.get_logger()


@asset(
    required_resource_keys={"bronze_io_manager", "silver_io_manager"},
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "operation": "extraction"},
)
def silver_extracted_content(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
    bronze_raw_html: dict,
) -> dict:
    """Extract clean content from bronze HTML.

    Skips URLs that already have extracted content (can be deleted to reprocess).

    Returns summary statistics.
    """
    bronze_io_manager = context.resources.bronze_io_manager
    silver_io_manager = context.resources.silver_io_manager
    extractor = ContentExtractor()

    total_urls = len(discovered_urls)
    context.log.info(f"Starting silver extraction for {total_urls} URLs")
    processed = 0
    cached = 0
    failed = 0

    for url_data in discovered_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        was_aggregator = url_data.get("was_aggregator", False)
        aggregator_info = {}
        if url_data.get("original_url"):
            aggregator_info = {
                "original_url": url_data.get("original_url"),
                "aggregator_type": url_data.get("aggregator_type"),
                "aggregator_title": url_data.get("aggregator_title"),
            }

        if silver_io_manager.exists("silver_extracted_content", url_hash):
            logger.info("silver.extraction.cache_hit", url_hash=url_hash, url=url)
            cached += 1
            continue

        # YouTube URLs don't need bronze layer
        is_youtube = ContentExtractor.is_youtube_url(url)

        if is_youtube:
            # YouTube: no bronze dependency
            bronze_data = None
            html_content = None
        else:
            # Regular URLs: require bronze layer
            if not bronze_io_manager.exists("bronze_raw_html", url_hash):
                logger.warning(
                    "silver.extraction.no_bronze",
                    url_hash=url_hash,
                    url=url,
                    was_aggregator=was_aggregator,
                    **aggregator_info,
                )
                failed += 1
                continue

            bronze_data = bronze_io_manager.load("bronze_raw_html", url_hash)
            html_content = bronze_data.get("html_content", "")

            if not html_content:
                logger.warning(
                    "silver.extraction.empty_html",
                    url_hash=url_hash,
                    url=url,
                    was_aggregator=was_aggregator,
                    **aggregator_info,
                )
                silver_data = {
                    "url": url,
                    "content_type": "unknown",
                    "title": "Extraction Failed - Empty Content",
                    "content": "",
                    "metadata": {},
                    "extraction_success": False,
                    "error_message": "Empty HTML content from bronze layer",
                    "lineage": {
                        "bronze_raw_html": bronze_data.get("download_info", {}),
                    },
                }
                silver_io_manager.save("silver_extracted_content", url_hash, silver_data)
                failed += 1
                continue

        logger.info(
            "silver.extraction.processing",
            url_hash=url_hash,
            url=url,
            was_aggregator=was_aggregator,
            **aggregator_info,
        )
        result = extractor.extract(ExtractionRequest(url=url, html_content=html_content))

        silver_data = {
            "url": result.url,
            "content_type": result.content_type,
            "title": result.title,
            "content": result.content,
            "metadata": result.metadata,
            "extraction_success": result.success,
            "error_message": result.error,
            "lineage": {
                "bronze_raw_html": bronze_data.get("download_info", {}) if bronze_data else {},
            },
        }

        silver_io_manager.save("silver_extracted_content", url_hash, silver_data)

        if result.success:
            content_length = len(result.content) if result.content else 0
            logger.info(
                "silver.extraction.success",
                url_hash=url_hash,
                url=url,
                title=result.title,
                content_type=result.content_type,
                content_length=content_length,
                was_aggregator=was_aggregator,
                **aggregator_info,
            )
            processed += 1
        else:
            logger.warning(
                "silver.extraction.failed",
                url_hash=url_hash,
                url=url,
                error=result.error,
                was_aggregator=was_aggregator,
                **aggregator_info,
            )
            failed += 1

    context.log.info(f"Silver extraction complete: {processed} extracted, {cached} cached, {failed} failed (total: {total_urls})")
    logger.info(
        "silver.extraction.complete",
        total=total_urls,
        processed=processed,
        cached=cached,
        failed=failed,
    )

    context.add_output_metadata(
        {
            "total_urls": total_urls,
            "processed": processed,
            "cached": cached,
            "failed": failed,
        }
    )

    return {
        "total_urls": total_urls,
        "processed": processed,
        "cached": cached,
        "failed": failed,
    }

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
    processed = 0
    cached = 0
    failed = 0

    for url_data in discovered_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if silver_io_manager.exists("silver_extracted_content", url_hash):
            logger.info("silver.extraction.cache_hit", url_hash=url_hash, url=url)
            cached += 1
            continue

        if not bronze_io_manager.exists("bronze_raw_html", url_hash):
            logger.warning(
                "silver.extraction.no_bronze",
                url_hash=url_hash,
                url=url,
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

        logger.info("silver.extraction.processing", url_hash=url_hash, url=url)
        result = extractor.extract(ExtractionRequest(url=url))

        silver_data = {
            "url": result.url,
            "content_type": result.content_type,
            "title": result.title,
            "content": result.content,
            "metadata": result.metadata,
            "extraction_success": result.success,
            "error_message": result.error,
            "lineage": {
                "bronze_raw_html": bronze_data.get("download_info", {}),
            },
        }

        silver_io_manager.save("silver_extracted_content", url_hash, silver_data)

        if result.success:
            processed += 1
        else:
            failed += 1

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

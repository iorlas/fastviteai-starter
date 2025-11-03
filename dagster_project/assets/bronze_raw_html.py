import structlog
from dagster import AssetExecutionContext, asset

from dagster_project.core.downloader import HTTPDownloader

logger = structlog.get_logger()


@asset(
    required_resource_keys={"bronze_io_manager"},
    compute_kind="python",
    group_name="bronze_layer",
    tags={"layer": "bronze", "source": "download"},
)
def bronze_raw_html(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> dict:
    """Download HTML content for discovered URLs.

    Skips URLs that already have cached HTML (bronze layer immutability).

    Returns summary statistics.
    """
    bronze_io_manager = context.resources.bronze_io_manager
    downloader = HTTPDownloader(timeout=30)

    total_urls = len(discovered_urls)
    context.log.info(f"Starting bronze layer download for {total_urls} URLs")
    processed = 0
    cached = 0
    failed = 0

    for url_data in discovered_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if bronze_io_manager.exists("bronze_raw_html", url_hash):
            logger.info("bronze.cache_hit", url_hash=url_hash, url=url)
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
            "bronze.downloading",
            url_hash=url_hash,
            url=url,
            was_aggregator=was_aggregator,
            **aggregator_info,
        )
        result = downloader.download(url)

        bronze_data = {
            "url": result.url,
            "url_hash": url_hash,
            "html_content": result.html_content,
            "download_info": {
                "status_code": result.status_code,
                "headers": result.headers,
                "download_timestamp": result.download_timestamp,
                "final_url": result.final_url,
                "error": result.error,
                "error_type": result.error_type,
            },
        }

        bronze_io_manager.save("bronze_raw_html", url_hash, bronze_data)

        if result.success:
            content_size = len(result.html_content) if result.html_content else 0
            logger.info(
                "bronze.download_success",
                url_hash=url_hash,
                url=url,
                status_code=result.status_code,
                content_size=content_size,
                was_aggregator=was_aggregator,
                **aggregator_info,
            )
            processed += 1
        else:
            logger.warning(
                "bronze.download_failed",
                url_hash=url_hash,
                url=url,
                error=result.error,
                error_type=result.error_type,
                status_code=result.status_code,
                was_aggregator=was_aggregator,
                **aggregator_info,
            )
            failed += 1

    context.log.info(f"Bronze layer complete: {processed} downloaded, {cached} cached, {failed} failed (total: {total_urls})")
    logger.info(
        "bronze.complete",
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

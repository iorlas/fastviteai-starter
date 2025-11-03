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

        logger.info("bronze.downloading", url_hash=url_hash, url=url)
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
            processed += 1
        else:
            failed += 1
            logger.warning(
                "bronze.download_failed",
                url_hash=url_hash,
                url=url,
                error=result.error,
            )

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

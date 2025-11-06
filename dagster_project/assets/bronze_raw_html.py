from dagster import AssetExecutionContext, asset

from dagster_project.config.constants import HTTP_TIMEOUT_DEFAULT
from dagster_project.core.downloader import HTTPDownloader
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.content_type import ContentType, detect_content_type


@asset(
    required_resource_keys={"bronze_io_manager"},
    compute_kind="python",
    group_name="bronze_layer",
    tags={"layer": "bronze", "source": "download", "content_type": "html"},
)
async def bronze_raw_html(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> dict:
    bronze_io_manager = context.resources.bronze_io_manager
    downloader = HTTPDownloader(timeout=HTTP_TIMEOUT_DEFAULT)

    html_urls = [u for u in discovered_urls if detect_content_type(u["url"]) == ContentType.HTML]

    stats = Stats(total=len(html_urls))
    context.log.info(f"Starting bronze HTML layer download for {stats.total} URLs")

    for url_data in html_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if bronze_io_manager.exists("bronze_raw_html", url_hash):
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        context.log.info(f"Downloading: {url}")
        result = await downloader.download(url)

        bronze_data = {
            "url": result.url,
            "url_hash": url_hash,
            "content_type": ContentType.HTML.value,
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
            context.log.info(f"✓ Downloaded: {url} ({content_size} bytes, status: {result.status_code})")
            stats.processed += 1
        else:
            context.log.warning(f"✗ Download failed: {url} - {result.error} (status: {result.status_code})")
            stats.failed += 1

    return stats.log_and_return(
        context, f"Bronze layer complete: {stats.processed} downloaded, {stats.cached} cached, {stats.failed} failed"
    )

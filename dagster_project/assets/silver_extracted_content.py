from dagster import AssetExecutionContext, asset

from dagster_project.core.content_extractor import ContentExtractor, ExtractionRequest
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.content_type import ContentType, detect_content_type


@asset(
    required_resource_keys={"bronze_io_manager", "silver_io_manager"},
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "operation": "extraction"},
)
async def silver_extracted_content(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
    bronze_raw_html: dict,
    bronze_raw_youtube: dict,
) -> dict:
    bronze_io_manager = context.resources.bronze_io_manager
    silver_io_manager = context.resources.silver_io_manager
    extractor = ContentExtractor()

    stats = Stats(total=len(discovered_urls))
    context.log.info(f"Starting silver extraction for {stats.total} URLs")

    for url_data in discovered_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if silver_io_manager.exists("silver_extracted_content", url_hash):
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        content_type = detect_content_type(url)

        if content_type == ContentType.YOUTUBE:
            if not bronze_io_manager.exists("bronze_raw_youtube", url_hash):
                context.log.warning(f"No bronze data for YouTube: {url}")
                stats.failed += 1
                continue

            bronze_data = bronze_io_manager.load("bronze_raw_youtube", url_hash)
            html_content = None

        elif content_type == ContentType.HTML:
            if not bronze_io_manager.exists("bronze_raw_html", url_hash):
                context.log.warning(f"No bronze data for HTML: {url}")
                stats.failed += 1
                continue

            bronze_data = bronze_io_manager.load("bronze_raw_html", url_hash)
            html_content = bronze_data.get("html_content", "")

            if not html_content:
                context.log.warning(f"Empty HTML content: {url}")
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
                stats.failed += 1
                continue
        else:
            context.log.error(f"Unknown content type {content_type.value}: {url}")
            stats.failed += 1
            continue

        context.log.info(f"Extracting: {url}")
        result = await extractor.extract(ExtractionRequest(url=url, html_content=html_content))

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
            context.log.info(f"✓ Extracted: {result.title} ({content_length} chars, type: {result.content_type})")
            stats.processed += 1
        else:
            context.log.warning(f"✗ Extraction failed: {url} - {result.error}")
            stats.failed += 1

    return stats.log_and_return(
        context, f"Silver extraction complete: {stats.processed} extracted, {stats.cached} cached, {stats.failed} failed"
    )

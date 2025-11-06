from datetime import UTC, datetime

from dagster import AssetExecutionContext, asset

from dagster_project.core.content_extractor import ContentExtractor, ExtractionRequest
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.content_type import ContentType
from dagster_project.utils.tables import BronzeTable, SilverTable


@asset(
    deps=["bronze_raw_html", "bronze_raw_youtube"],
    required_resource_keys={"bronze_storage", "silver_storage"},
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "operation": "extraction"},
)
async def silver_extracted_content(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> None:
    bronze_storage = context.resources.bronze_storage
    silver_storage = context.resources.silver_storage
    extractor = ContentExtractor()

    stats = Stats(total=len(discovered_urls))
    context.log.info(f"Starting silver extraction for {stats.total} URLs")

    for url_data in discovered_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if silver_storage.exists(SilverTable.EXTRACTED_CONTENT, url_hash):
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        content_type = url_data["content_type"]

        if content_type == ContentType.YOUTUBE.value:
            if not bronze_storage.exists(BronzeTable.RAW_YOUTUBE, url_hash):
                context.log.warning(f"No bronze data for YouTube: {url}")
                stats.failed += 1
                continue

            bronze_data = bronze_storage.load(BronzeTable.RAW_YOUTUBE, url_hash)
            html_content = None

        elif content_type == ContentType.HTML.value:
            if not bronze_storage.exists(BronzeTable.RAW_HTML, url_hash):
                context.log.warning(f"No bronze data for HTML: {url}")
                stats.failed += 1
                continue

            bronze_data = bronze_storage.load(BronzeTable.RAW_HTML, url_hash)
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
                    "created_at": datetime.now(UTC).isoformat(),
                    "updated_at": datetime.now(UTC).isoformat(),
                }
                silver_storage.save(SilverTable.EXTRACTED_CONTENT, url_hash, silver_data)
                stats.failed += 1
                continue
        else:
            context.log.error(f"Unknown content type {content_type}: {url}")
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
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        silver_storage.save(SilverTable.EXTRACTED_CONTENT, url_hash, silver_data)

        if result.success:
            content_length = len(result.content) if result.content else 0
            context.log.info(f"✓ Extracted: {result.title} ({content_length} chars, type: {result.content_type})")
            stats.processed += 1
        else:
            context.log.warning(f"✗ Extraction failed: {url} - {result.error}")
            stats.failed += 1

    context.log.info(f"Silver extraction complete: {stats.processed} extracted, {stats.cached} cached, {stats.failed} failed")
    context.add_output_metadata(stats.model_dump())

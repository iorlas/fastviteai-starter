from dagster import AssetExecutionContext, asset

from dagster_project.core.content_types.generic_html import GenericHTMLExtractor
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.tables import BronzeTable


@asset(
    required_resource_keys={"bronze_storage"},
    compute_kind="python",
    group_name="bronze_layer",
    tags={"layer": "bronze", "source": "download", "content_type": "html"},
)
async def bronze_html(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> None:
    bronze_storage = context.resources.bronze_storage
    extractor = GenericHTMLExtractor()

    html_urls = [u for u in discovered_urls if u["content_type"] == "html"]

    stats = Stats(total=len(html_urls))
    context.log.info(f"Starting bronze HTML extraction for {stats.total} URLs")

    for url_data in html_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if bronze_storage.exists(BronzeTable.HTML, url_hash):
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        context.log.info(f"Extracting: {url}")
        result = await extractor.extract(url)

        bronze_data = {**result.model_dump(), "url_hash": url_hash}

        bronze_storage.save(BronzeTable.HTML, url_hash, bronze_data)

        if result.success:
            content_length = len(result.content) if result.content else 0
            context.log.info(f"✓ Extracted: {result.title} ({content_length} chars)")
            stats.processed += 1
        else:
            context.log.warning(f"✗ Extraction failed: {url} - {result.error}")
            stats.failed += 1

    context.log.info(f"Bronze HTML extraction complete: {stats.processed} extracted, {stats.cached} cached, {stats.failed} failed")
    context.add_output_metadata(stats.model_dump())

import structlog
from dagster import AssetExecutionContext, asset

from dagster_project.core.content_extractor import ContentExtractor, ExtractionRequest
from dagster_project.partitions import url_partitions

logger = structlog.get_logger()


@asset(
    partitions_def=url_partitions,
    io_manager_key="silver_io_manager",
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "operation": "extraction"},
)
def silver_extracted_content(
    context: AssetExecutionContext,
    bronze_raw_html: dict,
) -> dict:
    url_hash = context.partition_key
    canonical_url = bronze_raw_html.get("url")

    if not canonical_url:
        msg = f"No URL found in bronze data for hash: {url_hash}"
        logger.error("silver.extraction.no_url", url_hash=url_hash)
        raise ValueError(msg)

    html_content_raw = bronze_raw_html.get("html_content", "")

    if not html_content_raw:
        logger.warning(
            "silver.extraction.empty_html",
            url_hash=url_hash,
            canonical_url=canonical_url,
        )
        return {
            "url": canonical_url,
            "url_hash": url_hash,
            "content_type": "unknown",
            "title": "Extraction Failed - Empty Content",
            "content": "",
            "metadata": {},
            "extraction_success": False,
            "error_message": "Empty HTML content from bronze layer",
            "lineage": {
                "bronze_raw_html": bronze_raw_html.get("download_info", {}),
            },
        }

    extractor = ContentExtractor()
    result = extractor.extract(ExtractionRequest(url=canonical_url))

    context.add_output_metadata(
        {
            "url": canonical_url,
            "content_type": result.content_type,
            "title": result.title,
            "content_length": len(result.content),
            "extraction_success": result.success,
        }
    )

    return {
        "url": result.url,
        "url_hash": url_hash,
        "content_type": result.content_type,
        "title": result.title,
        "content": result.content,
        "metadata": result.metadata,
        "extraction_success": result.success,
        "error_message": result.error,
        "lineage": {
            "bronze_raw_html": bronze_raw_html.get("download_info", {}),
        },
    }

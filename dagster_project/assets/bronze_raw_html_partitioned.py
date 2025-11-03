import structlog
from dagster import AssetExecutionContext, asset

from dagster_project.core.downloader import HTTPDownloader
from dagster_project.partitions import url_partitions
from dagster_project.utils.paths import BRONZE_URL_MAPPING_DIR

logger = structlog.get_logger()


@asset(
    partitions_def=url_partitions,
    io_manager_key="bronze_io_manager",
    compute_kind="python",
    group_name="bronze_layer",
    tags={"layer": "bronze", "source": "download"},
)
def bronze_raw_html(context: AssetExecutionContext) -> dict:
    url_hash = context.partition_key
    mapping_file = BRONZE_URL_MAPPING_DIR / f"{url_hash}.txt"

    if not mapping_file.exists():
        msg = f"No URL mapping found for hash: {url_hash}"
        logger.error("bronze.no_mapping", url_hash=url_hash)
        raise ValueError(msg)

    canonical_url = mapping_file.read_text().strip()

    downloader = HTTPDownloader(timeout=30)
    result = downloader.download(canonical_url)

    context.add_output_metadata(
        {
            "url": canonical_url,
            "status_code": result.status_code,
            "content_length": len(result.html_content),
            "final_url": result.final_url,
            "success": result.success,
        }
    )

    return {
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

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import httpx
import structlog
from dagster import AssetExecutionContext, Field, asset

logger = structlog.get_logger()


@asset(
    io_manager_key="bronze_io_manager",
    config_schema={
        "project_root": Field(str, is_required=False),
    },
    compute_kind="python",
    group_name="bronze_layer",
    tags={"layer": "bronze", "source": "download"},
)
def bronze_raw_html(context: AssetExecutionContext, bronze_raw_links: list) -> list:
    """Download and cache raw HTML for URLs from bronze_raw_links.

    Implements file-based caching: checks if HTML already exists before downloading.
    Stores error metadata for failed downloads to enable graceful degradation.

    Args:
        context: Dagster asset execution context
        bronze_raw_links: List of URLs to download (from upstream asset)

    Returns:
        List of dicts with metadata for each URL (success or error)
    """
    project_root_str = context.op_execution_context.op_config.get("project_root")
    if project_root_str:
        project_root = Path(project_root_str)
    else:
        project_root = Path(__file__).parent.parent.parent

    bronze_html_dir = project_root / "artifacts" / "bronze" / "raw_html"
    bronze_html_dir.mkdir(parents=True, exist_ok=True)

    results = []
    cache_hits = 0
    cache_misses = 0
    errors = 0

    logger.info(
        "bronze_layer.raw_html.started",
        url_count=len(bronze_raw_links),
    )

    for url in bronze_raw_links:
        # Compute full SHA256 hash for filename
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        html_file = bronze_html_dir / f"{url_hash}.json"

        # Check cache
        if html_file.exists():
            logger.debug(
                "bronze_layer.raw_html.cache_hit",
                url=url,
                hash=url_hash[:16],
            )
            cache_hits += 1
            continue

        # Cache miss - download HTML
        try:
            logger.info(
                "bronze_layer.raw_html.downloading",
                url=url,
                hash=url_hash[:16],
            )

            response = httpx.get(url, timeout=30, follow_redirects=True)
            response.raise_for_status()

            result = {
                "url": url,
                "html_content": response.text,
                "download_info": {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "download_timestamp": datetime.now(UTC).isoformat(),
                    "final_url": str(response.url),
                },
            }

            results.append(result)
            cache_misses += 1

            logger.info(
                "bronze_layer.raw_html.downloaded",
                url=url,
                status_code=response.status_code,
                content_length=len(response.text),
                hash=url_hash[:16],
            )

        except httpx.HTTPError as e:
            logger.warning(
                "bronze_layer.raw_html.http_error",
                url=url,
                error=str(e),
                error_type=type(e).__name__,
            )

            # Store error metadata
            result = {
                "url": url,
                "html_content": "",
                "download_info": {
                    "status_code": getattr(e.response, "status_code", None)
                    if hasattr(e, "response")
                    else None,
                    "headers": {},
                    "download_timestamp": datetime.now(UTC).isoformat(),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            }

            results.append(result)
            errors += 1

        except Exception as e:
            logger.error(
                "bronze_layer.raw_html.unexpected_error",
                url=url,
                error=str(e),
                error_type=type(e).__name__,
            )

            # Store error metadata
            result = {
                "url": url,
                "html_content": "",
                "download_info": {
                    "status_code": None,
                    "headers": {},
                    "download_timestamp": datetime.now(UTC).isoformat(),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            }

            results.append(result)
            errors += 1

    logger.info(
        "bronze_layer.raw_html.complete",
        total_urls=len(bronze_raw_links),
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        errors=errors,
        new_downloads=cache_misses,
    )

    context.add_output_metadata(
        {
            "total_urls": len(bronze_raw_links),
            "cache_hits": cache_hits,
            "new_downloads": cache_misses,
            "errors": errors,
        }
    )

    return results

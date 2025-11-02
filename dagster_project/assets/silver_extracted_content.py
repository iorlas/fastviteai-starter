import hashlib
from datetime import UTC, datetime

import structlog
from dagster import AssetExecutionContext, asset

from dagster_project.ops.html_extractor import (
    HTMLExtractionError,
    extract_html_from_cached,
)
from dagster_project.ops.youtube_extractor import (
    YouTubeExtractionError,
    extract_youtube_content,
)

logger = structlog.get_logger()


def is_youtube_url(url: str) -> bool:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    return parsed.netloc in ["youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"]


@asset(
    io_manager_key="silver_io_manager",
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "source": "extraction"},
)
def silver_extracted_content(context: AssetExecutionContext, bronze_raw_html: list) -> list:
    results = []
    html_count = 0
    youtube_count = 0
    errors = 0

    logger.info(
        "silver_layer.extraction.started",
        url_count=len(bronze_raw_html),
    )

    for html_data in bronze_raw_html:
        url = html_data["url"]
        url_hash = hashlib.sha256(url.encode()).hexdigest()

        # Check for errors from bronze layer
        if "error" in html_data.get("download_info", {}):
            logger.warning(
                "silver_layer.extraction.skipped_bronze_error",
                url=url,
                error=html_data["download_info"]["error"],
            )
            errors += 1
            continue

        try:
            if is_youtube_url(url):
                # Extract YouTube content (no caching for videos)
                logger.info("silver_layer.extraction.youtube", url=url)
                yt_content = extract_youtube_content(url)

                extracted = {
                    "url": url,
                    "type": "youtube",
                    "title": yt_content.title,
                    "content": yt_content.transcript,
                    "metadata": {
                        "author": yt_content.channel,
                        "published_date": None,
                        "word_count": len(yt_content.transcript.split()),
                        "extraction_method": "yt-dlp",
                        "channel": yt_content.channel,
                        "duration": yt_content.duration,
                        "description": yt_content.description,
                    },
                    "lineage": {
                        "source_asset": "bronze_raw_html",
                        "source_hash": url_hash,
                        "transformation_timestamp": datetime.now(UTC).isoformat(),
                    },
                }

                results.append(extracted)
                youtube_count += 1

                logger.info(
                    "silver_layer.extraction.youtube_complete",
                    url=url,
                    title=yt_content.title,
                )

            else:
                # Extract HTML content from bronze cache
                logger.info("silver_layer.extraction.html", url=url)

                html_content = html_data.get("html_content", "")
                if not html_content:
                    logger.warning(
                        "silver_layer.extraction.empty_html",
                        url=url,
                    )
                    errors += 1
                    continue

                html_result = extract_html_from_cached(html_content, url)

                extracted = {
                    "url": url,
                    "type": "html",
                    "title": html_result.title,
                    "content": html_result.content,
                    "metadata": {
                        "author": html_result.author,
                        "published_date": html_result.publish_date,
                        "word_count": len(html_result.content.split()),
                        "extraction_method": "beautifulsoup",
                    },
                    "lineage": {
                        "source_asset": "bronze_raw_html",
                        "source_hash": url_hash,
                        "transformation_timestamp": datetime.now(UTC).isoformat(),
                    },
                }

                results.append(extracted)
                html_count += 1

                logger.info(
                    "silver_layer.extraction.html_complete",
                    url=url,
                    title=html_result.title,
                    content_length=len(html_result.content),
                )

        except (HTMLExtractionError, YouTubeExtractionError) as e:
            logger.error(
                "silver_layer.extraction.failed",
                url=url,
                error=str(e),
                error_type=type(e).__name__,
            )
            errors += 1

        except Exception as e:
            logger.error(
                "silver_layer.extraction.unexpected_error",
                url=url,
                error=str(e),
                error_type=type(e).__name__,
            )
            errors += 1

    logger.info(
        "silver_layer.extraction.complete",
        total_urls=len(bronze_raw_html),
        html_count=html_count,
        youtube_count=youtube_count,
        errors=errors,
        successful=html_count + youtube_count,
    )

    context.add_output_metadata(
        {
            "total_urls": len(bronze_raw_html),
            "html_count": html_count,
            "youtube_count": youtube_count,
            "errors": errors,
            "successful": html_count + youtube_count,
        }
    )

    return results

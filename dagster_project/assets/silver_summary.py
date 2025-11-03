import structlog
from dagster import AssetExecutionContext, asset

from dagster_project.core.summarizer import SummaryRequest

logger = structlog.get_logger()


@asset(
    required_resource_keys={"summary_generator", "silver_io_manager"},
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "operation": "summarization"},
)
def silver_summary(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
    silver_extracted_content: dict,
    silver_discussions: dict,
) -> dict:
    """Generate AI summaries from extracted content.

    Skips URLs that already have summaries (can be deleted to regenerate).

    Returns summary statistics.
    """
    silver_io_manager = context.resources.silver_io_manager
    summary_generator = context.resources.summary_generator

    total_urls = len(discovered_urls)
    context.log.info(f"Starting AI summarization for {total_urls} URLs using model: {summary_generator.generator.model}")
    processed = 0
    cached = 0
    failed = 0

    for url_data in discovered_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if silver_io_manager.exists("silver_summary", url_hash):
            logger.info("silver.summary.cache_hit", url_hash=url_hash, url=url)
            cached += 1
            continue

        if not silver_io_manager.exists("silver_extracted_content", url_hash):
            logger.warning(
                "silver.summary.no_extracted_content",
                url_hash=url_hash,
                url=url,
            )
            failed += 1
            continue

        extracted_content = silver_io_manager.load("silver_extracted_content", url_hash)

        if not extracted_content.get("extraction_success"):
            logger.warning(
                "silver.summary.skip_failed_extraction",
                url_hash=url_hash,
                url=url,
            )

            summary_data = {
                "url": url,
                "title": extracted_content.get("title", "Unknown"),
                "status": "failed",
                "error": extracted_content.get("error_message", "Content extraction failed"),
                "error_type": "ExtractionError",
                "content_type": extracted_content.get("content_type", "unknown"),
                "lineage": {
                    "silver_extracted_content": {
                        "extraction_success": False,
                        "error": extracted_content.get("error_message"),
                    },
                },
            }
            silver_io_manager.save("silver_summary", url_hash, summary_data)
            failed += 1
            continue

        title = extracted_content.get("title", url)

        discussion_data = None
        discussion_metadata = None
        if silver_io_manager.exists("silver_discussions", url_hash):
            try:
                discussion_data_full = silver_io_manager.load("silver_discussions", url_hash)
                discussion_data = discussion_data_full.get("comments", [])
                discussion_metadata = discussion_data_full.get("metadata", {})
                logger.info(
                    "silver.summary.with_discussions",
                    url_hash=url_hash,
                    comments=len(discussion_data),
                )
            except Exception as e:
                logger.warning(
                    "silver.summary.discussion_load_failed",
                    url_hash=url_hash,
                    error=str(e),
                )

        context.log.info(f"Summarizing: {title[:80]}...")
        logger.info(
            "silver.summary.processing",
            url_hash=url_hash,
            url=url,
            title=title,
            model=summary_generator.generator.model,
            has_discussions=discussion_data is not None,
        )

        try:
            result = summary_generator.generator.generate(
                SummaryRequest(
                    content=extracted_content.get("content", ""),
                    title=title,
                    content_type=extracted_content.get("content_type", "unknown"),
                    url=url,
                    discussions=discussion_data,
                    discussion_metadata=discussion_metadata,
                )
            )

            summary_data = {
                "url": url,
                "title": title,
                "status": "success",
                "content_type": extracted_content.get("content_type", "unknown"),
                "structured_summary": result.structured_summary.model_dump(),
                "model": result.model,
                "tokens_used": result.tokens_used,
                "latency_ms": result.latency_ms,
                "lineage": {
                    "silver_extracted_content": {
                        "extraction_success": True,
                        "content_length": len(extracted_content.get("content", "")),
                    },
                },
            }
            silver_io_manager.save("silver_summary", url_hash, summary_data)
            context.log.info(f"✓ Summary generated ({result.tokens_used} tokens, {result.latency_ms}ms)")
            processed += 1

        except Exception as e:
            context.log.error(f"Summary failed for {title[:50]}: {type(e).__name__} - {str(e)}")
            logger.error(
                "silver.summary.failed",
                url_hash=url_hash,
                url=url,
                error=str(e),
                error_type=type(e).__name__,
            )

            summary_data = {
                "url": url,
                "title": title,
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "content_type": extracted_content.get("content_type", "unknown"),
                "lineage": {
                    "silver_extracted_content": {
                        "extraction_success": True,
                    },
                },
            }
            silver_io_manager.save("silver_summary", url_hash, summary_data)
            failed += 1

    context.log.info(f"✓ Summarization complete: {processed} generated, {cached} cached, {failed} failed (total: {total_urls})")
    logger.info(
        "silver.summary.complete",
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

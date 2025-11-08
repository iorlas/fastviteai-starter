from datetime import UTC, datetime

from dagster import AssetExecutionContext, asset

from dagster_project.core.summarizer import SummaryRequest
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.tables import SilverTable


@asset(
    deps=["silver_extracted_content", "silver_discussions"],
    required_resource_keys={"summary_generator", "silver_storage"},
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "operation": "summarization"},
)
async def silver_summary(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> None:
    silver_storage = context.resources.silver_storage
    summary_generator = context.resources.summary_generator

    stats = Stats(total=len(discovered_urls))
    context.log.info(f"Starting AI summarization for {stats.total} URLs using model: {summary_generator.generator.model}")

    for url_data in discovered_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        # CRITICAL: Keep this cache check to prevent wasteful OpenAI API calls ($$$)
        # Unlike other silver assets, summarization is expensive (~$0.005/article)
        # and non-deterministic. Other silver assets regenerate cheaply from bronze.
        if silver_storage.exists(SilverTable.SUMMARIES, url_hash):
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        if not silver_storage.exists(SilverTable.EXTRACTED_CONTENT, url_hash):
            context.log.warning(f"No extracted content: {url}")
            stats.failed += 1
            continue

        extracted_content = silver_storage.load(SilverTable.EXTRACTED_CONTENT, url_hash)

        if not extracted_content.get("extraction_success"):
            context.log.warning(f"Skipping failed extraction: {url}")

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
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
            silver_storage.save(SilverTable.SUMMARIES, url_hash, summary_data)
            stats.failed += 1
            continue

        title = extracted_content.get("title", url)

        discussion_data = None
        discussion_metadata = None
        if silver_storage.exists(SilverTable.DISCUSSIONS, url_hash):
            try:
                discussion_data_full = silver_storage.load(SilverTable.DISCUSSIONS, url_hash)
                discussion_data = discussion_data_full.get("comments", [])
                discussion_metadata = discussion_data_full.get("metadata", {})
                context.log.info(f"Loaded discussions: {len(discussion_data)} comments")
            except Exception as e:
                context.log.warning(f"Discussion load failed: {e}")

        context.log.info(f"Summarizing: {title[:80]}...")

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
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
            silver_storage.save(SilverTable.SUMMARIES, url_hash, summary_data)
            context.log.info(f"✓ Summary generated ({result.tokens_used} tokens, {result.latency_ms}ms)")
            stats.processed += 1

        except Exception as e:
            context.log.error(f"Summary failed for {title[:50]}: {type(e).__name__} - {str(e)}")

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
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
            silver_storage.save(SilverTable.SUMMARIES, url_hash, summary_data)
            stats.failed += 1

    context.log.info(f"Summarization complete: {stats.processed} generated, {stats.cached} cached, {stats.failed} failed")
    context.add_output_metadata(stats.model_dump())

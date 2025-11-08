from datetime import UTC, datetime

from dagster import AssetExecutionContext, asset

from dagster_project.config import settings
from dagster_project.core.summary import compile_summary_input
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.tables import SilverTable


@asset(
    deps=["bronze_html", "bronze_youtube", "bronze_discussions"],
    required_resource_keys={"summary_generator", "bronze_storage", "silver_storage"},
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "operation": "summarization"},
)
async def silver_summary(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> None:
    if not settings.enable_summarization:
        context.log.info("Summarization disabled via ENABLE_SUMMARIZATION environment variable")
        return None

    bronze_storage = context.resources.bronze_storage
    silver_storage = context.resources.silver_storage
    summary_generator = context.resources.summary_generator

    stats = Stats(total=len(discovered_urls))
    context.log.info(f"Starting AI summarization for {stats.total} URLs using model: {summary_generator.generator.model}")

    for url_data in discovered_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if silver_storage.exists(SilverTable.SUMMARIES, url_hash):
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        try:
            summary_input = compile_summary_input(url, bronze_storage.base_dir)

            if summary_input.discussions:
                num_stories = len(summary_input.discussions)
                total_comments = sum(d.get("comment_count", 0) for d in summary_input.discussions)
                context.log.info(f"Loaded {num_stories} discussion(s) with {total_comments} total comments")

            context.log.info(f"Summarizing: {summary_input.title[:80]}...")

            result = summary_generator.generator.generate(summary_input)

            summary_data = {
                "url": url,
                "title": summary_input.title,
                "status": "success",
                "content_type": summary_input.content_type,
                "structured_summary": result.structured_summary.model_dump(),
                "model": result.model,
                "tokens_used": result.tokens_used,
                "latency_ms": result.latency_ms,
                "lineage": {
                    "content_type": summary_input.content_type,
                    "extraction_success": True,
                    "content_length": len(summary_input.content),
                },
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
            silver_storage.save(SilverTable.SUMMARIES, url_hash, summary_data)
            context.log.info(f"✓ Summary generated ({result.tokens_used} tokens, {result.latency_ms}ms)")
            stats.processed += 1

        except ValueError as e:
            context.log.warning(f"Skipping {url}: {str(e)}")

            summary_data = {
                "url": url,
                "title": url_data.get("url", "Unknown"),
                "status": "failed",
                "error": str(e),
                "error_type": "CompilationError",
                "content_type": url_data.get("content_type", "unknown"),
                "lineage": {
                    "extraction_success": False,
                    "error": str(e),
                },
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
            silver_storage.save(SilverTable.SUMMARIES, url_hash, summary_data)
            stats.failed += 1

        except Exception as e:
            context.log.error(f"Summary failed for {url}: {type(e).__name__} - {str(e)}")

            summary_data = {
                "url": url,
                "title": url_data.get("url", "Unknown"),
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "content_type": url_data.get("content_type", "unknown"),
                "lineage": {
                    "extraction_success": True,
                },
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
            silver_storage.save(SilverTable.SUMMARIES, url_hash, summary_data)
            stats.failed += 1

    context.log.info(f"Summarization complete: {stats.processed} generated, {stats.cached} cached, {stats.failed} failed")
    context.add_output_metadata(stats.model_dump())

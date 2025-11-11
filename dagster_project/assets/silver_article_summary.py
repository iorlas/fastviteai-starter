import json
from datetime import UTC, datetime

from dagster import AssetExecutionContext, asset

from dagster_project.config import settings
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.paths import get_article_summary_path
from dagster_project.utils.tables import BronzeTable


@asset(
    deps=["bronze_html", "bronze_youtube_transcription"],
    required_resource_keys={"article_summarizer", "bronze_storage"},
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "operation": "article_summarization", "stage": "1"},
)
async def silver_article_summary(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> None:
    if not settings.enable_summarization:
        context.log.info("Summarization disabled via ENABLE_SUMMARIZATION environment variable")
        return None

    bronze_storage = context.resources.bronze_storage
    article_summarizer = context.resources.article_summarizer

    stats = Stats(total=len(discovered_urls))
    context.log.info(f"Stage 1: Starting article summarization for {stats.total} URLs")

    for url_data in discovered_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]
        content_type = url_data["content_type"]

        # Check cache
        article_summary_path = get_article_summary_path(url_hash)
        if article_summary_path.exists():
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        try:
            # Load bronze content (HTML or YouTube)
            bronze_content = None
            if content_type == "html" and bronze_storage.exists(BronzeTable.HTML, url_hash):
                bronze_content = bronze_storage.load(BronzeTable.HTML, url_hash)
            elif content_type == "youtube" and bronze_storage.exists(BronzeTable.YOUTUBE, url_hash):
                bronze_content = bronze_storage.load(BronzeTable.YOUTUBE, url_hash)

            if not bronze_content:
                context.log.warning(f"No bronze content found for {url}")
                stats.failed += 1
                continue

            if not bronze_content.get("success"):
                error_msg = bronze_content.get("error", "Content extraction failed")
                context.log.warning(f"Skipping {url}: Bronze extraction failed - {error_msg}")
                stats.failed += 1
                continue

            # Extract fields
            title = bronze_content.get("title", url)
            content = bronze_content.get("content", "")
            content_type_label = bronze_content.get("content_type", content_type)

            context.log.info(f"Summarizing article: {title[:80]}...")

            # Stage 1: Article-only analysis
            article_analysis = await article_summarizer.summarize(
                content=content,
                title=title,
                url=url,
                content_type=content_type_label,
            )

            # Save article summary
            article_data = {
                "url": url,
                "url_hash": url_hash,
                "title": title,
                "content_type": content_type_label,
                "analysis": article_analysis.model_dump(),
                "created_at": datetime.now(UTC).isoformat(),
            }

            article_summary_path.parent.mkdir(parents=True, exist_ok=True)
            article_summary_path.write_text(json.dumps(article_data, indent=2, default=str))

            context.log.info(f"✓ Article summary generated: {title[:50]}")
            stats.processed += 1

        except ValueError as e:
            context.log.warning(f"Skipping {url}: {str(e)}")
            stats.failed += 1

        except Exception as e:
            context.log.error(f"Article summary failed for {url}: {type(e).__name__} - {str(e)}")
            stats.failed += 1

    context.log.info(f"Stage 1 complete: {stats.processed} generated, {stats.cached} cached, {stats.failed} failed")
    context.add_output_metadata(stats.model_dump())

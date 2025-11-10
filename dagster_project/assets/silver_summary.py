import json
from datetime import UTC, datetime

from dagster import AssetExecutionContext, asset

from dagster_project.config import settings
from dagster_project.core.summary.schema import ArticleAnalysis, CommunityTake
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.paths import get_article_summary_path, get_discussion_summary_dir
from dagster_project.utils.tables import SilverTable


@asset(
    deps=["silver_article_summary", "silver_discussion_summary"],
    required_resource_keys={"community_synthesizer", "silver_storage"},
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "operation": "community_synthesis", "stage": "3"},
)
async def silver_summary(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> None:
    if not settings.enable_summarization:
        context.log.info("Summarization disabled via ENABLE_SUMMARIZATION environment variable")
        return None

    silver_storage = context.resources.silver_storage
    community_synthesizer = context.resources.community_synthesizer

    stats = Stats(total=len(discovered_urls))
    context.log.info(f"Stage 3: Starting community synthesis for {stats.total} URLs")

    for url_data in discovered_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        # Check cache
        if silver_storage.exists(SilverTable.SUMMARIES, url_hash):
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        try:
            # Load article summary from Stage 1
            article_summary_path = get_article_summary_path(url_hash)
            if not article_summary_path.exists():
                context.log.warning(f"No article summary found for {url} - skipping")
                stats.failed += 1
                continue

            article_data = json.loads(article_summary_path.read_text())
            article_analysis = ArticleAnalysis(**article_data["analysis"])

            # Load discussion summaries from Stage 2
            discussion_summaries_dir = get_discussion_summary_dir(url_hash)
            discussion_summaries = []

            if discussion_summaries_dir.exists():
                for summary_file in discussion_summaries_dir.glob("*.json"):
                    discussion_data = json.loads(summary_file.read_text())
                    community_take = CommunityTake(**discussion_data["community_take"])
                    discussion_summaries.append(community_take)

            # Synthesize based on number of discussions
            if len(discussion_summaries) == 0:
                # No discussions - save article analysis as-is (community=None)
                context.log.info("No discussions found - saving article-only analysis")
                final_analysis = article_analysis

            elif len(discussion_summaries) == 1:
                # Single discussion - use directly (skip Stage 3 LLM call)
                context.log.info("Single discussion found - using directly without synthesis")
                article_analysis.community = discussion_summaries[0]
                final_analysis = article_analysis

            else:
                # Multiple discussions - synthesize
                context.log.info(f"Synthesizing {len(discussion_summaries)} discussions for {url}")
                semantic_summary = article_analysis.article.semantic_summary
                synthesized_community = await community_synthesizer.synthesize(
                    discussion_summaries=discussion_summaries,
                    semantic_summary=semantic_summary,
                )
                article_analysis.community = synthesized_community
                final_analysis = article_analysis

            # Save final summary
            summary_data = {
                "url": url,
                "title": article_data["title"],
                "status": "success",
                "content_type": article_data["content_type"],
                "structured_summary": final_analysis.model_dump(),
                "discussion_count": len(discussion_summaries),
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }

            silver_storage.save(SilverTable.SUMMARIES, url_hash, summary_data)
            context.log.info(f"✓ Final summary generated ({len(discussion_summaries)} discussions)")
            stats.processed += 1

        except Exception as e:
            context.log.error(f"Summary synthesis failed for {url}: {type(e).__name__} - {str(e)}")

            # Save error state
            summary_data = {
                "url": url,
                "title": url_data.get("url", "Unknown"),
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "content_type": url_data.get("content_type", "unknown"),
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
            silver_storage.save(SilverTable.SUMMARIES, url_hash, summary_data)
            stats.failed += 1

    context.log.info(f"Stage 3 complete: {stats.processed} generated, {stats.cached} cached, {stats.failed} failed")
    context.add_output_metadata(stats.model_dump())

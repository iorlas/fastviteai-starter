import json
from datetime import UTC, datetime
from pathlib import Path

from dagster import AssetExecutionContext, asset

from dagster_project.config import settings
from dagster_project.core.discussions.unified_models import UnifiedDiscussion
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.paths import get_article_summary_path, get_discussion_summary_path
from dagster_project.utils.tables import BronzeTable


@asset(
    deps=["bronze_discussions", "silver_article_summary"],
    required_resource_keys={"discussion_summarizer", "bronze_storage"},
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "operation": "discussion_summarization", "stage": "2"},
)
async def silver_discussion_summary(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> None:
    if not settings.enable_summarization:
        context.log.info("Summarization disabled via ENABLE_SUMMARIZATION environment variable")
        return None

    bronze_storage = context.resources.bronze_storage
    discussion_summarizer = context.resources.discussion_summarizer

    stats = Stats(total=0)  # Will count total discussions
    total_discussions = 0

    context.log.info(f"Stage 2: Starting discussion summarization for {len(discovered_urls)} URLs")

    for url_data in discovered_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        # Load article summary to get semantic_summary
        article_summary_path = get_article_summary_path(url_hash)
        if not article_summary_path.exists():
            context.log.warning(f"No article summary found for {url} - skipping discussion analysis")
            continue

        article_data = json.loads(article_summary_path.read_text())
        article_analysis = article_data.get("analysis", {})
        article_metadata = article_analysis.get("article", {})
        semantic_summary = article_metadata.get("semantic_summary")

        if not semantic_summary:
            context.log.warning(f"No semantic_summary in article analysis for {url} - skipping")
            continue

        # Load discussions from bronze
        discussions_dir = Path(bronze_storage.base_dir) / BronzeTable.DISCUSSIONS / url_hash
        if not discussions_dir.exists():
            context.log.debug(f"No discussions found for {url}")
            continue

        # Process each discussion
        discussion_files = [f for f in discussions_dir.glob("*.json") if f.name != "metadata.json"]
        stats.total += len(discussion_files)
        total_discussions += len(discussion_files)

        context.log.info(f"Processing {len(discussion_files)} discussion(s) for {url}")

        for discussion_file in discussion_files:
            # Load discussion
            discussion_dict = json.loads(discussion_file.read_text())
            discussion = UnifiedDiscussion(**discussion_dict)

            # Skip discussions with 0 comments (no community input to analyze)
            if discussion.comment_count == 0:
                context.log.debug(f"Skipping 0-comment discussion: {discussion.platform}/{discussion.id}")
                stats.skipped += 1
                continue

            # Build path for this discussion summary
            discussion_summary_path = get_discussion_summary_path(url_hash, discussion.platform, discussion.id)

            # Check cache
            if discussion_summary_path.exists():
                context.log.debug(f"Cache hit: {discussion.platform} discussion {discussion.id}")
                stats.cached += 1
                continue

            context.log.info(f"Analyzing {discussion.platform} discussion: {discussion.title[:50]} ({discussion.comment_count} comments)")

            # Stage 2: Analyze discussion with article context
            community_take = await discussion_summarizer.analyze_discussion(
                discussion=discussion,
                semantic_summary=semantic_summary,
            )

            # Save discussion summary
            discussion_data = {
                "url": url,
                "url_hash": url_hash,
                "platform": discussion.platform,
                "discussion_id": discussion.id,
                "discussion_url": discussion.discussion_url,
                "comment_count": discussion.comment_count,
                "community_take": community_take.model_dump(),
                "created_at": datetime.now(UTC).isoformat(),
            }

            discussion_summary_path.parent.mkdir(parents=True, exist_ok=True)
            discussion_summary_path.write_text(json.dumps(discussion_data, indent=2, default=str))

            context.log.info(f"✓ Discussion summary generated: {discussion.platform}/{discussion.id}")
            stats.processed += 1

    context.log.info(
        f"Stage 2 complete: {stats.processed} generated, {stats.cached} cached, "
        f"{stats.skipped} skipped (0 comments), {stats.failed} failed (total {total_discussions} discussions)"
    )
    result = stats.model_dump()
    result["total_discussions"] = total_discussions
    context.add_output_metadata(result)

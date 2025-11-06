import json
from pathlib import Path

from dagster import AssetExecutionContext, asset

from dagster_project.core.discussions.lobsters_models import LobstersStoryFull
from dagster_project.core.discussions.models import (
    DiscussionMetadata,
    HNStoryFull,
)
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.discussion_utils import load_stories_from_dir


@asset(
    required_resource_keys={"bronze_io_manager", "silver_io_manager"},
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "operation": "discussion_extraction"},
)
async def silver_discussions(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
    bronze_discussions: dict,
) -> dict:
    bronze_io_manager = context.resources.bronze_io_manager
    silver_io_manager = context.resources.silver_io_manager
    base_dir = Path(bronze_io_manager.base_dir) / "bronze_discussions"

    stats = Stats(total=len(discovered_urls))
    total_comments_extracted = 0
    context.log.info(f"Starting discussion extraction for {stats.total} URLs")

    for url_data in discovered_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if silver_io_manager.exists("silver_discussions", url_hash):
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        url_dir = base_dir / url_hash
        metadata_file = url_dir / "metadata.json"

        if not metadata_file.exists():
            context.log.info(f"No discussions in bronze: {url}")
            stats.cached += 1
            continue

        try:
            context.log.info(f"Extracting discussions: {url}")

            with metadata_file.open() as f:
                metadata_dict = json.load(f)
            metadata = DiscussionMetadata(**metadata_dict)

            hn_stories = load_stories_from_dir(url_dir, metadata.hn_story_ids, HNStoryFull, "HN", context.log.info)
            lobsters_stories = load_stories_from_dir(
                url_dir, metadata.lobsters_story_ids, LobstersStoryFull, "Lobsters", context.log.warning
            )

            all_stories = hn_stories + lobsters_stories
            total_comments = sum(story.count_total_comments() for story in all_stories)

            silver_data = {
                "url": url,
                "url_hash": url_hash,
                "metadata": metadata.model_dump(),
                "stories": [s.model_dump() for s in all_stories],
                "total_comments": total_comments,
                "lineage": {
                    "bronze_discussions": {
                        "total_stories": metadata.total_stories,
                        "discovered_at": metadata.discovered_at.isoformat(),
                    }
                },
            }

            silver_io_manager.save("silver_discussions", url_hash, silver_data)
            context.log.info(f"✓ Extracted {total_comments} comments from {metadata.total_stories} discussion(s)")
            stats.processed += 1
            total_comments_extracted += total_comments

        except Exception as e:
            context.log.error(f"✗ Failed to extract: {url} - {str(e)}")
            stats.failed += 1

    result = stats.model_dump()
    result["total_comments_extracted"] = total_comments_extracted

    context.log.info(f"Discussion extraction complete: {stats.processed} processed, {stats.cached} cached, {stats.failed} failed")
    context.add_output_metadata(result)
    return result

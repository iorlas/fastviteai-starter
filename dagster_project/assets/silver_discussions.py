from datetime import UTC, datetime

from dagster import AssetExecutionContext, asset

from dagster_project.core.discussions.lobsters_models import LobstersStoryFull
from dagster_project.core.discussions.models import (
    DiscussionMetadata,
    HNStoryFull,
)
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.tables import BronzeTable, SilverTable


@asset(
    deps=["bronze_discussions"],
    required_resource_keys={"bronze_storage", "silver_storage"},
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "operation": "discussion_extraction"},
)
async def silver_discussions(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> None:
    bronze_storage = context.resources.bronze_storage
    silver_storage = context.resources.silver_storage

    stats = Stats(total=len(discovered_urls))
    total_comments_extracted = 0
    context.log.info(f"Starting discussion extraction for {stats.total} URLs")

    for url_data in discovered_urls:
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if silver_storage.exists(SilverTable.DISCUSSIONS, url_hash):
            context.log.info(f"Cache hit: {url}")
            stats.cached += 1
            continue

        if not bronze_storage.exists(BronzeTable.DISCUSSIONS, "metadata", sub_partition=url_hash):
            context.log.info(f"No discussions in bronze: {url}")
            stats.cached += 1
            continue

        try:
            context.log.info(f"Extracting discussions: {url}")

            metadata_dict = bronze_storage.load(BronzeTable.DISCUSSIONS, "metadata", sub_partition=url_hash)
            metadata = DiscussionMetadata(**metadata_dict)

            all_stories = []
            for story_id in metadata.hn_story_ids:
                story_data = bronze_storage.load(BronzeTable.DISCUSSIONS, str(story_id), sub_partition=url_hash)
                all_stories.append(HNStoryFull(**story_data))

            for story_id in metadata.lobsters_story_ids:
                story_data = bronze_storage.load(BronzeTable.DISCUSSIONS, str(story_id), sub_partition=url_hash)
                all_stories.append(LobstersStoryFull(**story_data))

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
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }

            silver_storage.save(SilverTable.DISCUSSIONS, url_hash, silver_data)
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

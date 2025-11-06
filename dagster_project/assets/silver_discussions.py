import json
from pathlib import Path

import structlog
from dagster import AssetExecutionContext, asset

from dagster_project.core.discussions.lobsters_models import LobstersStoryFull
from dagster_project.core.discussions.models import (
    DiscussionMetadata,
    HNStoryFull,
)

logger = structlog.get_logger()


@asset(
    required_resource_keys={"bronze_io_manager", "silver_io_manager"},
    compute_kind="python",
    group_name="silver_layer",
    tags={"layer": "silver", "operation": "discussion_extraction"},
)
def silver_discussions(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
    bronze_discussions: dict,
) -> dict:
    bronze_io_manager = context.resources.bronze_io_manager
    silver_io_manager = context.resources.silver_io_manager
    base_dir = Path(bronze_io_manager.base_dir) / "bronze_discussions"

    total_urls = len(discovered_urls)
    context.log.info(f"Starting discussion extraction for {total_urls} URLs")
    processed = 0
    cached = 0
    no_discussions = 0
    failed = 0
    total_comments_extracted = 0

    for idx, url_data in enumerate(discovered_urls, 1):
        url = url_data["url"]
        url_hash = url_data["url_hash"]

        if silver_io_manager.exists("silver_discussions", url_hash):
            logger.info("silver.discussions.cache_hit", url_hash=url_hash, url=url)
            context.log.info(f"[{idx}/{total_urls}] Cached discussions: {url}")
            cached += 1
            continue

        url_dir = base_dir / url_hash
        metadata_file = url_dir / "metadata.json"

        if not metadata_file.exists():
            logger.info(
                "silver.discussions.no_bronze",
                url_hash=url_hash,
                url=url,
            )
            context.log.info(f"[{idx}/{total_urls}] No discussions in bronze: {url}")
            no_discussions += 1
            continue

        try:
            context.log.info(f"[{idx}/{total_urls}] Extracting discussions: {url}")

            with metadata_file.open() as f:
                metadata_dict = json.load(f)
            metadata = DiscussionMetadata(**metadata_dict)

            all_stories = []

            for story_id in metadata.hn_story_ids:
                story_file = url_dir / f"{story_id}.json"

                if not story_file.exists():
                    logger.warning(
                        "silver.discussions.story_file_missing",
                        url_hash=url_hash,
                        story_id=story_id,
                        platform="hackernews",
                    )
                    continue

                with story_file.open() as f:
                    story_dict = json.load(f)

                story = HNStoryFull(**story_dict)
                all_stories.append(story)

                logger.info(
                    "silver.discussions.story_processed",
                    url_hash=url_hash,
                    story_id=story_id,
                    comments_root=len(story.children),
                    platform="hackernews",
                )

            for story_id in metadata.lobsters_story_ids:
                story_file = url_dir / f"{story_id}.json"

                if not story_file.exists():
                    logger.warning(
                        "silver.discussions.story_file_missing",
                        url_hash=url_hash,
                        story_id=story_id,
                        platform="lobsters",
                    )
                    continue

                with story_file.open() as f:
                    story_dict = json.load(f)

                story = LobstersStoryFull(**story_dict)
                all_stories.append(story)

                logger.info(
                    "silver.discussions.story_processed",
                    url_hash=url_hash,
                    story_id=story_id,
                    comments_root=len(story.comments),
                    platform="lobsters",
                )

            def count_comments(comments: list) -> int:
                count = len(comments)
                for comment in comments:
                    if hasattr(comment, "children"):
                        count += count_comments(comment.children)
                return count

            def get_story_comments(story) -> list:
                if isinstance(story, HNStoryFull):
                    return story.children
                elif isinstance(story, LobstersStoryFull):
                    return story.comments
                return []

            total_comments = sum(count_comments(get_story_comments(story)) for story in all_stories)

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

            logger.info(
                "silver.discussions.success",
                url_hash=url_hash,
                url=url,
                total_comments=total_comments,
                stories=metadata.total_stories,
            )

            context.log.info(f"[{idx}/{total_urls}] ✓ Extracted {total_comments} comments from {metadata.total_stories} discussion(s)")

            processed += 1
            total_comments_extracted += total_comments

        except Exception as e:
            logger.error(
                "silver.discussions.extraction_failed",
                url_hash=url_hash,
                url=url,
                error=str(e),
                error_type=type(e).__name__,
            )
            context.log.error(f"[{idx}/{total_urls}] ✗ Failed to extract: {url} - {str(e)}")
            failed += 1

    context.log.info(
        f"Discussion extraction complete: {processed} processed, {cached} cached, "
        f"{no_discussions} no discussions, {failed} failed (total: {total_urls})"
    )
    logger.info(
        "silver.discussions.complete",
        total=total_urls,
        processed=processed,
        cached=cached,
        no_discussions=no_discussions,
        failed=failed,
        total_comments_extracted=total_comments_extracted,
    )

    context.add_output_metadata(
        {
            "total_urls": total_urls,
            "processed": processed,
            "cached": cached,
            "no_discussions": no_discussions,
            "failed": failed,
            "total_comments_extracted": total_comments_extracted,
        }
    )

    return {
        "total_urls": total_urls,
        "processed": processed,
        "cached": cached,
        "no_discussions": no_discussions,
        "failed": failed,
        "total_comments_extracted": total_comments_extracted,
    }

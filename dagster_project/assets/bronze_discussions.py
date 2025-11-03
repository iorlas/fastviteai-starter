import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import structlog
from dagster import AssetExecutionContext, asset

from dagster_project.core.discussions.hn_client import HNClient
from dagster_project.core.discussions.models import DiscussionMetadata

logger = structlog.get_logger()


async def _fetch_discussions(discovered_urls: list[dict], base_dir: Path, progress_callback=None) -> dict:
    total_urls = len(discovered_urls)
    processed = 0
    cached = 0
    failed = 0
    total_stories = 0
    total_comments = 0

    async with HNClient() as hn_client:
        for idx, url_data in enumerate(discovered_urls, 1):
            url = url_data["url"]
            url_hash = url_data["url_hash"]

            url_dir = base_dir / url_hash
            metadata_file = url_dir / "metadata.json"

            if metadata_file.exists():
                logger.info("discussions.cache_hit", url_hash=url_hash, url=url)
                if progress_callback:
                    progress_callback(f"[{idx}/{total_urls}] Cached: {url}")
                cached += 1
                continue

            logger.info("discussions.discovering", url_hash=url_hash, url=url)
            if progress_callback:
                progress_callback(f"[{idx}/{total_urls}] Discovering discussions for: {url}")

            try:
                stories = await hn_client.search_by_url(url)

                if not stories:
                    logger.info("discussions.no_stories_found", url_hash=url_hash, url=url)
                    if progress_callback:
                        progress_callback(f"[{idx}/{total_urls}] No HN discussions found for: {url}")
                    continue

                url_dir.mkdir(parents=True, exist_ok=True)

                story_ids = []
                story_comments = 0

                if progress_callback:
                    progress_callback(f"[{idx}/{total_urls}] Found {len(stories)} HN discussion(s), fetching comments...")

                for story in stories:
                    story_full = await hn_client.fetch_story_with_comments(story.story_id)
                    story_full_dict = story_full.model_dump()

                    story_file = url_dir / f"{story.story_id}.json"
                    with story_file.open("w") as f:
                        json.dump(story_full_dict, f, indent=2, default=str)

                    story_ids.append(story.story_id)
                    comment_count = hn_client._count_comments(story_full.children)
                    story_comments += comment_count

                metadata = DiscussionMetadata(
                    url=url,
                    url_hash=url_hash,
                    total_stories=len(stories),
                    total_comments=story_comments,
                    platforms=["hackernews"],
                    hn_story_ids=story_ids,
                    discovered_at=datetime.now(UTC),
                    cache_ttl_hours=24,
                )

                with metadata_file.open("w") as f:
                    json.dump(metadata.model_dump(), f, indent=2, default=str)

                logger.info(
                    "discussions.discovery_success",
                    url_hash=url_hash,
                    url=url,
                    stories=len(stories),
                    comments=story_comments,
                )

                if progress_callback:
                    progress_callback(f"[{idx}/{total_urls}] ✓ Saved {story_comments} comments from {len(stories)} discussion(s)")

                processed += 1
                total_stories += len(stories)
                total_comments += story_comments

            except Exception as e:
                logger.error(
                    "discussions.discovery_failed",
                    url_hash=url_hash,
                    url=url,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                if progress_callback:
                    progress_callback(f"[{idx}/{total_urls}] ✗ Failed: {url} - {str(e)}")
                failed += 1

    return {
        "total_urls": total_urls,
        "processed": processed,
        "cached": cached,
        "failed": failed,
        "total_stories": total_stories,
        "total_comments": total_comments,
    }


@asset(
    required_resource_keys={"bronze_io_manager"},
    compute_kind="python",
    group_name="bronze_layer",
    tags={"layer": "bronze", "source": "discussions"},
)
def bronze_discussions(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> dict:
    bronze_io_manager = context.resources.bronze_io_manager
    base_dir = Path(bronze_io_manager.base_dir) / "bronze_discussions"
    base_dir.mkdir(parents=True, exist_ok=True)

    total_urls = len(discovered_urls)
    context.log.info(f"Starting discussion discovery for {total_urls} URLs")

    result = asyncio.run(_fetch_discussions(discovered_urls, base_dir, context.log.info))

    context.log.info(
        f"Discussion discovery complete: {result['processed']} processed, "
        f"{result['cached']} cached, {result['failed']} failed (total: {total_urls})"
    )
    logger.info(
        "discussions.complete",
        total=total_urls,
        processed=result["processed"],
        cached=result["cached"],
        failed=result["failed"],
        total_stories=result["total_stories"],
        total_comments=result["total_comments"],
    )

    context.add_output_metadata(
        {
            "total_urls": total_urls,
            "processed": result["processed"],
            "cached": result["cached"],
            "failed": result["failed"],
            "total_stories": result["total_stories"],
            "total_comments": result["total_comments"],
        }
    )

    return result

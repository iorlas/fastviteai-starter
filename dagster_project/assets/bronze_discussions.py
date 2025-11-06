import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import structlog
from dagster import AssetExecutionContext, asset

from dagster_project.core.discussions.hn_client import HNClient
from dagster_project.core.discussions.lobsters_client import LobstersClient
from dagster_project.core.discussions.models import DiscussionLink, DiscussionMetadata

logger = structlog.get_logger()


async def _fetch_discussions(discovered_urls: list[dict], base_dir: Path, progress_callback=None) -> dict:
    total_urls = len(discovered_urls)
    processed = 0
    cached = 0
    failed = 0
    total_stories = 0

    async with HNClient() as hn_client, LobstersClient() as lobsters_client:
        for idx, url_data in enumerate(discovered_urls, 1):
            url = url_data["url"]
            url_hash = url_data["url_hash"]
            pre_saved_links = [DiscussionLink(**link) for link in url_data.get("discussion_links", [])]

            url_dir = base_dir / url_hash
            metadata_file = url_dir / "metadata.json"

            if metadata_file.exists():
                logger.info("discussions.cache_hit", url_hash=url_hash, url=url)
                if progress_callback:
                    progress_callback(f"[{idx}/{total_urls}] Cached: {url}")
                cached += 1
                continue

            logger.info("discussions.discovering", url_hash=url_hash, url=url, pre_saved_links=len(pre_saved_links))
            if progress_callback:
                progress_callback(f"[{idx}/{total_urls}] Discovering discussions for: {url}")

            try:
                all_discussion_urls = set()
                hn_story_ids = []
                lobsters_story_ids = []
                platforms = []

                for link in pre_saved_links:
                    all_discussion_urls.add(link.url)

                hn_stories = await hn_client.search_by_url(url)
                for story in hn_stories:
                    hn_url = f"https://news.ycombinator.com/item?id={story.story_id}"
                    all_discussion_urls.add(hn_url)

                lobsters_urls = await lobsters_client.search_by_url(url)
                all_discussion_urls.update(lobsters_urls)

                if not all_discussion_urls:
                    logger.info("discussions.no_stories_found", url_hash=url_hash, url=url)
                    if progress_callback:
                        progress_callback(f"[{idx}/{total_urls}] No discussions found for: {url}")
                    continue

                url_dir.mkdir(parents=True, exist_ok=True)

                if progress_callback:
                    progress_callback(f"[{idx}/{total_urls}] Found {len(all_discussion_urls)} unique discussion(s), fetching comments...")

                for disc_url in all_discussion_urls:
                    if "news.ycombinator.com" in disc_url:
                        story_id = int(disc_url.split("id=")[1].split("&")[0])
                        if story_id not in hn_story_ids:
                            story_full = await hn_client.fetch_story_with_comments(story_id)
                            story_file = url_dir / f"{story_id}.json"
                            with story_file.open("w") as f:
                                json.dump(story_full.model_dump(), f, indent=2, default=str)
                            hn_story_ids.append(story_id)
                            if "hackernews" not in platforms:
                                platforms.append("hackernews")

                    elif "lobste.rs" in disc_url:
                        short_id = LobstersClient.extract_short_id_from_url(disc_url)
                        if short_id and short_id not in lobsters_story_ids:
                            story_full = await lobsters_client.fetch_story_with_comments(short_id)
                            story_file = url_dir / f"{short_id}.json"
                            with story_file.open("w") as f:
                                json.dump(story_full.model_dump(), f, indent=2, default=str)
                            lobsters_story_ids.append(short_id)
                            if "lobsters" not in platforms:
                                platforms.append("lobsters")

                final_discussion_links = [
                    DiscussionLink(type="hackernews", url=f"https://news.ycombinator.com/item?id={sid}") for sid in hn_story_ids
                ] + [DiscussionLink(type="lobsters", url=f"https://lobste.rs/s/{sid}") for sid in lobsters_story_ids]

                metadata = DiscussionMetadata(
                    url=url,
                    url_hash=url_hash,
                    total_stories=len(hn_story_ids) + len(lobsters_story_ids),
                    platforms=platforms,
                    hn_story_ids=hn_story_ids,
                    lobsters_story_ids=lobsters_story_ids,
                    discussion_links=final_discussion_links,
                    discovered_at=datetime.now(UTC),
                    cache_ttl_hours=24,
                )

                with metadata_file.open("w") as f:
                    json.dump(metadata.model_dump(), f, indent=2, default=str)

                logger.info(
                    "discussions.discovery_success",
                    url_hash=url_hash,
                    url=url,
                    total_stories=metadata.total_stories,
                    hn_stories=len(hn_story_ids),
                    lobsters_stories=len(lobsters_story_ids),
                )

                if progress_callback:
                    hn_count = len(hn_story_ids)
                    lobsters_count = len(lobsters_story_ids)
                    progress_callback(
                        f"[{idx}/{total_urls}] ✓ Saved {metadata.total_stories} discussion(s) (HN: {hn_count}, Lobsters: {lobsters_count})"
                    )

                processed += 1
                total_stories += metadata.total_stories

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
    )

    context.add_output_metadata(
        {
            "total_urls": total_urls,
            "processed": result["processed"],
            "cached": result["cached"],
            "failed": result["failed"],
            "total_stories": result["total_stories"],
        }
    )

    return result

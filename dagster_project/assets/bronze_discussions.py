from datetime import UTC, datetime

from dagster import AssetExecutionContext, asset

from dagster_project.core.discussions.hn_client import HackerNewsClient
from dagster_project.core.discussions.lobsters_client import LobstersClient
from dagster_project.core.discussions.models import DiscussionLink, DiscussionMetadata
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.tables import BronzeTable


async def _fetch_discussions(discovered_urls: list[dict], storage, progress_callback=None) -> dict:
    stats = Stats(total=len(discovered_urls))
    total_stories = 0

    async with HackerNewsClient() as hn, LobstersClient() as lobsters:
        for url_data in discovered_urls:
            url = url_data["url"]
            url_hash = url_data["url_hash"]
            pre_saved_links = [DiscussionLink(**link) for link in url_data.get("discussion_links", [])]

            if storage.exists(BronzeTable.DISCUSSIONS, "metadata", sub_partition=url_hash):
                if progress_callback:
                    progress_callback(f"Cached: {url}")
                stats.cached += 1
                continue

            if progress_callback:
                progress_callback(f"Discovering discussions for: {url}")

            try:
                all_discussion_urls = {link.url for link in pre_saved_links}

                hn_urls = await hn.search_by_url(url)
                lobsters_urls = await lobsters.search_by_url(url)
                all_discussion_urls.update(hn_urls)
                all_discussion_urls.update(lobsters_urls)

                if not all_discussion_urls:
                    if progress_callback:
                        progress_callback(f"No discussions found for: {url}")
                    continue

                if progress_callback:
                    progress_callback(f"Found {len(all_discussion_urls)} unique discussion(s), fetching comments...")

                hn_story_ids = []
                lobsters_story_ids = []

                for disc_url in all_discussion_urls:
                    if "news.ycombinator.com" in disc_url:
                        story_id = hn.extract_story_id(disc_url)
                        if story_id not in hn_story_ids:
                            story_full = await hn.fetch_story(disc_url, story_id)
                            story_data = {
                                **story_full.model_dump(),
                                "created_at": datetime.now(UTC).isoformat(),
                            }
                            storage.save(BronzeTable.DISCUSSIONS, story_id, story_data, sub_partition=url_hash)
                            hn_story_ids.append(story_id)

                    elif "lobste.rs" in disc_url:
                        story_id = lobsters.extract_story_id(disc_url)
                        if story_id not in lobsters_story_ids:
                            story_full = await lobsters.fetch_story(disc_url, story_id)
                            story_data = {
                                **story_full.model_dump(),
                                "created_at": datetime.now(UTC).isoformat(),
                            }
                            storage.save(BronzeTable.DISCUSSIONS, story_id, story_data, sub_partition=url_hash)
                            lobsters_story_ids.append(story_id)

                platforms = []
                if hn_story_ids:
                    platforms.append("hackernews")
                if lobsters_story_ids:
                    platforms.append("lobsters")

                final_discussion_links = [hn.build_discussion_link(sid) for sid in hn_story_ids] + [
                    lobsters.build_discussion_link(sid) for sid in lobsters_story_ids
                ]

                metadata = DiscussionMetadata(
                    url=url,
                    total_stories=len(hn_story_ids) + len(lobsters_story_ids),
                    platforms=platforms,
                    hn_story_ids=hn_story_ids,
                    lobsters_story_ids=lobsters_story_ids,
                    discussion_links=final_discussion_links,
                    discovered_at=datetime.now(UTC),
                    cache_ttl_hours=24,
                )

                metadata_data = {
                    **metadata.model_dump(),
                    "created_at": datetime.now(UTC).isoformat(),
                }
                storage.save(BronzeTable.DISCUSSIONS, "metadata", metadata_data, sub_partition=url_hash)

                if progress_callback:
                    progress_callback(
                        f"✓ Saved {metadata.total_stories} discussion(s) (HN: {len(hn_story_ids)}, Lobsters: {len(lobsters_story_ids)})"
                    )

                stats.processed += 1
                total_stories += metadata.total_stories

            except Exception as e:
                if progress_callback:
                    progress_callback(f"✗ Failed: {url} - {str(e)}")
                stats.failed += 1

    result = stats.model_dump()
    result["total_stories"] = total_stories
    return result


@asset(
    required_resource_keys={"bronze_storage"},
    compute_kind="python",
    group_name="bronze_layer",
    tags={"layer": "bronze", "source": "discussions"},
)
async def bronze_discussions(
    context: AssetExecutionContext,
    discovered_urls: list[dict],
) -> None:
    bronze_storage = context.resources.bronze_storage

    context.log.info(f"Starting discussion discovery for {len(discovered_urls)} URLs")
    result = await _fetch_discussions(discovered_urls, bronze_storage, context.log.info)

    context.log.info(
        f"Discussion discovery complete: {result['processed']} processed, "
        f"{result['cached']} cached, {result['failed']} failed, {result['total_stories']} total stories"
    )
    context.add_output_metadata(result)

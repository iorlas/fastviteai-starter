from datetime import UTC, datetime

from dagster import AssetExecutionContext, asset

from dagster_project.core.discussions.discussion_fetcher import fetch_discussions_for_url
from dagster_project.core.discussions.hn_client import HackerNewsClient
from dagster_project.core.discussions.lobsters_client import LobstersClient
from dagster_project.core.discussions.shared_models import DiscussionLink, DiscussionMetadata
from dagster_project.utils.asset_utils import Stats
from dagster_project.utils.tables import BronzeTable


async def _process_url_discussions(url_data: dict, clients: list, storage, progress_callback) -> int:
    url = url_data["url"]
    url_hash = url_data["url_hash"]

    if storage.exists(BronzeTable.DISCUSSIONS, "metadata", sub_partition=url_hash):
        progress_callback(f"Cached: {url}")
        return 0

    pre_saved_links = [DiscussionLink(**link) for link in url_data.get("discussion_links", [])]

    result = await fetch_discussions_for_url(url, clients, pre_saved_links)

    # Save all unified discussions
    for discussion in result.discussions:
        storage.save(BronzeTable.DISCUSSIONS, discussion.id, discussion.model_dump(), sub_partition=url_hash)

    metadata = DiscussionMetadata(
        url=url,
        discussion_links=result.discussion_links,
        discovered_at=datetime.now(UTC),
    )

    storage.save(BronzeTable.DISCUSSIONS, "metadata", metadata.model_dump(), sub_partition=url_hash)

    total_stories = len(result.discussions)
    progress_callback(f"✓ Saved {total_stories} discussion(s)")

    return total_stories


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
    stats = Stats(total=len(discovered_urls))
    total_stories = 0

    context.log.info(f"Starting discussion discovery for {len(discovered_urls)} URLs")

    async with HackerNewsClient() as hn, LobstersClient() as lobsters:
        clients = [hn, lobsters]

        for url_data in discovered_urls:
            try:
                story_count = await _process_url_discussions(url_data, clients, bronze_storage, context.log.info)
                stats.processed += 1
                total_stories += story_count

            except Exception as e:
                context.log.info(f"✗ Failed: {url_data['url']} - {str(e)}")
                stats.failed += 1

    result = stats.model_dump()
    result["total_stories"] = total_stories

    context.log.info(
        f"Discussion discovery complete: {result['processed']} processed, "
        f"{result['failed']} failed, {result['total_stories']} total stories"
    )
    context.add_output_metadata(result)

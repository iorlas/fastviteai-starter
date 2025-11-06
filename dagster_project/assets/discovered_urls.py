from pathlib import Path

from dagster import AssetExecutionContext, Config, asset
from pydantic import Field
from url_normalize import url_normalize

from dagster_project.core.aggregator_resolver import resolve_url
from dagster_project.core.extractors.watchers import RSSWatcher, RSSWatcherError
from dagster_project.utils.paths import MANUAL_LINKS_FILE, MONITORING_LINKS_FILE
from dagster_project.utils.url_utils import compute_url_hash


class DiscoveredUrlsConfig(Config):
    source_type: str = Field(
        default="both",
        description="Source type: 'manual', 'watchers', or 'both'",
    )


def read_links_from_file(file_path: Path) -> list[str]:
    if not file_path.exists():
        return []

    links = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                links.append(line)

    return links


async def _process_discovered_url(
    url: str,
    source: str,
    seen_hashes: set[str],
    discovered_list: list[dict],
    context: AssetExecutionContext,
) -> bool:
    resolution_result = await resolve_url(url)
    normalized = url_normalize(resolution_result.resolved_url.strip())
    canonical_url = normalized if normalized else resolution_result.resolved_url.strip()
    url_hash = compute_url_hash(canonical_url)

    if url_hash in seen_hashes:
        return False

    url_data = {
        "url": canonical_url,
        "url_hash": url_hash,
        "source": source,
        "discussion_links": [link.model_dump() for link in resolution_result.discussion_links],
    }

    if resolution_result.was_aggregator:
        url_data["original_url"] = resolution_result.original_url
        url_data["aggregator_type"] = resolution_result.aggregator_type
        url_data["aggregator_title"] = resolution_result.title

        context.log.info(
            f"Aggregator resolved: {resolution_result.aggregator_type} '{resolution_result.title}' -> {canonical_url} (source: {source})"
        )
    else:
        context.log.info(f"URL added: {canonical_url} (source: {source})")

    discovered_list.append(url_data)
    seen_hashes.add(url_hash)
    return True


@asset(
    compute_kind="python",
    group_name="discovery",
    tags={"layer": "discovery", "source": "ingestion"},
)
async def discovered_urls(context: AssetExecutionContext, config: DiscoveredUrlsConfig) -> list[dict]:
    context.log.info(f"Starting URL discovery with source_type={config.source_type}")
    discovered_urls_list = []
    seen_hashes = set()

    if config.source_type in ("manual", "both"):
        manual_links = read_links_from_file(MANUAL_LINKS_FILE)
        context.log.info(f"Found {len(manual_links)} manual links from {MANUAL_LINKS_FILE.name}")

        for url in manual_links:
            await _process_discovered_url(url, "manual", seen_hashes, discovered_urls_list, context)

    if config.source_type in ("watchers", "both"):
        monitoring_urls = read_links_from_file(MONITORING_LINKS_FILE)
        context.log.info(f"Found {len(monitoring_urls)} monitoring URLs from {MONITORING_LINKS_FILE.name}")

        watcher = RSSWatcher()
        for feed_url in monitoring_urls:
            is_rss_feed = any(pattern in feed_url.lower() for pattern in [".xml", ".rss", "/feed", "/rss", "feeds/", "atom.xml"])

            if is_rss_feed:
                context.log.info(f"Processing RSS feed: {feed_url}")
                try:
                    discovered_links = watcher.fetch_links(feed_url)
                    context.log.info(f"Discovered {len(discovered_links)} URLs from RSS feed: {feed_url}")

                    for url in discovered_links:
                        await _process_discovered_url(url, f"rss:{feed_url}", seen_hashes, discovered_urls_list, context)

                except RSSWatcherError as e:
                    context.log.warning(f"Failed to fetch RSS feed {feed_url}: {e}")
            else:
                await _process_discovered_url(feed_url, "monitoring_direct", seen_hashes, discovered_urls_list, context)

    context.log.info(f"Discovery complete: {len(discovered_urls_list)} unique URLs found (source: {config.source_type})")

    context.add_output_metadata(
        {
            "total_urls": len(discovered_urls_list),
            "source_type": config.source_type,
        }
    )

    return discovered_urls_list

from pathlib import Path

import structlog
from dagster import AssetExecutionContext, Config, asset
from pydantic import Field

from dagster_project.core.aggregator_resolver import resolve_url
from dagster_project.core.extractors.watchers import RSSWatcher, RSSWatcherError
from dagster_project.utils.paths import MANUAL_LINKS_FILE, MONITORING_LINKS_FILE
from dagster_project.utils.url_utils import compute_url_hash, normalize_url

logger = structlog.get_logger()


class DiscoveredUrlsConfig(Config):
    """Configuration for discovered_urls asset."""

    source_type: str = Field(
        default="both",
        description="Source type: 'manual', 'watchers', or 'both'",
    )


def read_links_from_file(file_path: Path) -> list[str]:
    """Read links from a text file, skipping comments and empty lines."""
    if not file_path.exists():
        return []

    links = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                links.append(line)

    return links


@asset(
    compute_kind="python",
    group_name="discovery",
    tags={"layer": "discovery", "source": "ingestion"},
)
def discovered_urls(context: AssetExecutionContext, config: DiscoveredUrlsConfig) -> list[dict]:
    """Discovery coordinator - finds URLs from configured sources.

    Returns list of discovered URLs with their metadata.
    Each URL is deduplicated and normalized.

    Returns:
        List of dicts with keys: url, url_hash, source
    """
    context.log.info(f"Starting URL discovery with source_type={config.source_type}")
    discovered_urls_list = []
    seen_hashes = set()

    if config.source_type in ("manual", "both"):
        manual_links = read_links_from_file(MANUAL_LINKS_FILE)
        context.log.info(f"Found {len(manual_links)} manual links from {MANUAL_LINKS_FILE.name}")
        logger.info("discovery.manual_links", count=len(manual_links))

        for url in manual_links:
            resolution_result = resolve_url(url)
            canonical_url = normalize_url(resolution_result.resolved_url)
            url_hash = compute_url_hash(canonical_url)

            if url_hash not in seen_hashes:
                url_data = {
                    "url": canonical_url,
                    "url_hash": url_hash,
                    "source": "manual",
                }

                if resolution_result.was_aggregator:
                    url_data["original_url"] = resolution_result.original_url
                    url_data["aggregator_type"] = resolution_result.aggregator_type
                    url_data["aggregator_title"] = resolution_result.title

                    logger.info(
                        "discovery.aggregator_resolved",
                        url_hash=url_hash,
                        original_url=resolution_result.original_url,
                        resolved_url=canonical_url,
                        aggregator_type=resolution_result.aggregator_type,
                        aggregator_title=resolution_result.title,
                        source="manual",
                    )
                else:
                    logger.info(
                        "discovery.url_added",
                        url_hash=url_hash,
                        url=canonical_url,
                        source="manual",
                    )

                discovered_urls_list.append(url_data)
                seen_hashes.add(url_hash)

    if config.source_type in ("watchers", "both"):
        monitoring_urls = read_links_from_file(MONITORING_LINKS_FILE)
        context.log.info(f"Found {len(monitoring_urls)} monitoring URLs from {MONITORING_LINKS_FILE.name}")
        logger.info("discovery.monitoring_urls", count=len(monitoring_urls))

        watcher = RSSWatcher()
        for feed_url in monitoring_urls:
            is_rss_feed = any(pattern in feed_url.lower() for pattern in [".xml", ".rss", "/feed", "/rss", "feeds/", "atom.xml"])

            if is_rss_feed:
                context.log.info(f"Processing RSS feed: {feed_url}")
                logger.info("discovery.rss_feed", feed_url=feed_url)
                try:
                    discovered_links = watcher.fetch_links(feed_url)
                    context.log.info(f"Discovered {len(discovered_links)} URLs from RSS feed: {feed_url}")
                    logger.info(
                        "discovery.rss_discovered",
                        feed_url=feed_url,
                        count=len(discovered_links),
                    )

                    for url in discovered_links:
                        resolution_result = resolve_url(url)
                        canonical_url = normalize_url(resolution_result.resolved_url)
                        url_hash = compute_url_hash(canonical_url)

                        if url_hash not in seen_hashes:
                            url_data = {
                                "url": canonical_url,
                                "url_hash": url_hash,
                                "source": f"rss:{feed_url}",
                            }

                            if resolution_result.was_aggregator:
                                url_data["original_url"] = resolution_result.original_url
                                url_data["aggregator_type"] = resolution_result.aggregator_type
                                url_data["aggregator_title"] = resolution_result.title

                                logger.info(
                                    "discovery.aggregator_resolved",
                                    url_hash=url_hash,
                                    original_url=resolution_result.original_url,
                                    resolved_url=canonical_url,
                                    aggregator_type=resolution_result.aggregator_type,
                                    aggregator_title=resolution_result.title,
                                    source=f"rss:{feed_url}",
                                )
                            else:
                                logger.info(
                                    "discovery.url_added",
                                    url_hash=url_hash,
                                    url=canonical_url,
                                    source=f"rss:{feed_url}",
                                )

                            discovered_urls_list.append(url_data)
                            seen_hashes.add(url_hash)

                except RSSWatcherError as e:
                    context.log.warning(f"Failed to fetch RSS feed {feed_url}: {e}")
                    logger.warning("discovery.rss_failed", feed_url=feed_url, error=str(e))
            else:
                resolution_result = resolve_url(feed_url)
                canonical_url = normalize_url(resolution_result.resolved_url)
                url_hash = compute_url_hash(canonical_url)

                if url_hash not in seen_hashes:
                    url_data = {
                        "url": canonical_url,
                        "url_hash": url_hash,
                        "source": "monitoring_direct",
                    }

                    if resolution_result.was_aggregator:
                        url_data["original_url"] = resolution_result.original_url
                        url_data["aggregator_type"] = resolution_result.aggregator_type
                        url_data["aggregator_title"] = resolution_result.title

                        logger.info(
                            "discovery.aggregator_resolved",
                            url_hash=url_hash,
                            original_url=resolution_result.original_url,
                            resolved_url=canonical_url,
                            aggregator_type=resolution_result.aggregator_type,
                            aggregator_title=resolution_result.title,
                            source="monitoring_direct",
                        )
                    else:
                        logger.info(
                            "discovery.url_added",
                            url_hash=url_hash,
                            url=canonical_url,
                            source="monitoring_direct",
                        )

                    discovered_urls_list.append(url_data)
                    seen_hashes.add(url_hash)

    context.log.info(f"Discovery complete: {len(discovered_urls_list)} unique URLs found (source: {config.source_type})")
    logger.info(
        "discovery.complete",
        total_urls=len(discovered_urls_list),
        source_type=config.source_type,
    )

    context.add_output_metadata(
        {
            "total_urls": len(discovered_urls_list),
            "source_type": config.source_type,
        }
    )

    return discovered_urls_list

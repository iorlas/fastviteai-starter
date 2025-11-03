from pathlib import Path

import structlog
from dagster import AssetExecutionContext, asset

from dagster_project.ops.watchers import RSSWatcher, RSSWatcherError
from dagster_project.partitions import compute_url_hash, normalize_url, url_partitions
from dagster_project.utils.paths import (
    BRONZE_URL_MAPPING_DIR,
    MANUAL_LINKS_FILE,
    MONITORING_LINKS_FILE,
)

logger = structlog.get_logger()


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


def write_url_mapping(url_hash: str, canonical_url: str) -> None:
    """Write URL hash to canonical URL mapping file."""
    BRONZE_URL_MAPPING_DIR.mkdir(parents=True, exist_ok=True)
    mapping_file = BRONZE_URL_MAPPING_DIR / f"{url_hash}.txt"
    mapping_file.write_text(canonical_url)


@asset(
    compute_kind="python",
    group_name="discovery",
    tags={"layer": "discovery", "source": "ingestion"},
)
def discovered_urls(context: AssetExecutionContext) -> dict:
    """Discovery coordinator - finds URLs from all sources and manages partitions.

    This asset:
    1. Discovers URLs from RSS feeds, manual lists, etc.
    2. Normalizes URLs and computes hashes
    3. Adds new URLs to dynamic partition definition
    4. Returns summary statistics

    Returns:
        Dict with discovery statistics and metadata
    """
    discovered_hashes = []
    total_discoveries = 0

    manual_links = read_links_from_file(MANUAL_LINKS_FILE)
    logger.info("discovery.manual_links", count=len(manual_links))

    for url in manual_links:
        canonical_url = normalize_url(url)
        url_hash = compute_url_hash(canonical_url)
        write_url_mapping(url_hash, canonical_url)
        discovered_hashes.append(url_hash)
        total_discoveries += 1

    monitoring_urls = read_links_from_file(MONITORING_LINKS_FILE)
    logger.info("discovery.monitoring_urls", count=len(monitoring_urls))

    watcher = RSSWatcher()
    for feed_url in monitoring_urls:
        is_rss_feed = any(pattern in feed_url.lower() for pattern in [".xml", ".rss", "/feed", "/rss", "feeds/", "atom.xml"])

        if is_rss_feed:
            logger.info("discovery.rss_feed", feed_url=feed_url)
            try:
                discovered_links = watcher.fetch_links(feed_url)
                logger.info(
                    "discovery.rss_discovered",
                    feed_url=feed_url,
                    count=len(discovered_links),
                )

                for url in discovered_links:
                    canonical_url = normalize_url(url)
                    url_hash = compute_url_hash(canonical_url)
                    write_url_mapping(url_hash, canonical_url)
                    discovered_hashes.append(url_hash)
                    total_discoveries += 1

            except RSSWatcherError as e:
                logger.warning("discovery.rss_failed", feed_url=feed_url, error=str(e))
        else:
            canonical_url = normalize_url(feed_url)
            url_hash = compute_url_hash(canonical_url)
            write_url_mapping(url_hash, canonical_url)
            discovered_hashes.append(url_hash)
            total_discoveries += 1

    unique_url_hashes = list(set(discovered_hashes))
    logger.info(
        "discovery.complete",
        total_discoveries=total_discoveries,
        unique_urls=len(unique_url_hashes),
    )

    existing_partitions = set(context.instance.get_dynamic_partitions(url_partitions.name))
    new_partitions = [url_hash for url_hash in unique_url_hashes if url_hash not in existing_partitions]

    if new_partitions:
        context.instance.add_dynamic_partitions(
            partitions_def_name=url_partitions.name,
            partition_keys=new_partitions,
        )
        logger.info("discovery.partitions_added", count=len(new_partitions))

    context.add_output_metadata(
        {
            "total_discoveries": total_discoveries,
            "unique_urls": len(unique_url_hashes),
            "new_partitions": len(new_partitions),
            "existing_partitions": len(existing_partitions),
        }
    )

    return {
        "total_discoveries": total_discoveries,
        "unique_url_hashes": unique_url_hashes,
        "new_partitions": new_partitions,
    }

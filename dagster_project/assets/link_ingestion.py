import hashlib
from pathlib import Path
from typing import NamedTuple

from dagster import AssetExecutionContext, Field, asset

from dagster_project.ops.watchers import RSSWatcher, RSSWatcherError


class LinkRecord(NamedTuple):
    url: str
    url_hash: str
    source_file: str


def compute_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def read_links_from_file(file_path: Path) -> list[str]:
    if not file_path.exists():
        return []

    links = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith("#"):
                links.append(line)

    return links


@asset(
    name="link_ingestion",
    config_schema={
        "source_filter": Field(str, default_value="both", is_required=False),
        "project_root": Field(str, is_required=False),
    },
)
def link_ingestion_asset(context: AssetExecutionContext) -> list[LinkRecord]:
    # Get source filter from config (default to "both" for backwards compatibility)
    source_filter = context.op_config.get("source_filter", "both")

    # Get project root from config or auto-detect
    project_root_str = context.op_config.get("project_root")
    if project_root_str:
        project_root = Path(project_root_str)
    else:
        project_root = Path(__file__).parent.parent.parent
    manual_file = project_root / "manual_links.txt"
    monitoring_file = project_root / "monitoring_list.txt"
    summaries_dir = project_root / "artifacts" / "summaries"

    # Ensure summaries directory exists
    summaries_dir.mkdir(parents=True, exist_ok=True)

    # Read links from files based on source_filter
    manual_links = []
    monitoring_links = []

    if source_filter in ("manual", "both"):
        manual_links = read_links_from_file(manual_file)
        context.log.info(f"Found {len(manual_links)} links in manual_links.txt")

    if source_filter in ("monitoring", "both"):
        monitoring_urls = read_links_from_file(monitoring_file)
        context.log.info(f"Found {len(monitoring_urls)} URLs in monitoring_list.txt")

        # Process monitoring URLs - some may be RSS feeds that need watcher processing
        watcher = RSSWatcher()
        for url in monitoring_urls:
            # Heuristic: Check if URL looks like an RSS feed
            is_rss_feed = any(
                pattern in url.lower()
                for pattern in [".xml", ".rss", "/feed", "/rss", "feeds/", "atom.xml"]
            )

            if is_rss_feed:
                context.log.info(f"Detected RSS feed: {url}")
                try:
                    # Use watcher to discover links from RSS feed
                    discovered_links = watcher.fetch_links(url)
                    context.log.info(
                        f"RSSWatcher discovered {len(discovered_links)} links from {url}"
                    )
                    monitoring_links.extend(discovered_links)
                except RSSWatcherError as e:
                    context.log.warning(f"Failed to fetch RSS feed {url}: {e}")
                    # Continue processing other URLs even if one RSS feed fails
            else:
                # Not an RSS feed, treat as regular link
                monitoring_links.append(url)

    # Process all links and filter out duplicates
    unprocessed_links = []
    seen_urls = set()

    for url in manual_links:
        if url in seen_urls:
            continue
        seen_urls.add(url)

        url_hash = compute_url_hash(url)
        summary_file = summaries_dir / f"{url_hash}.json"

        if not summary_file.exists():
            unprocessed_links.append(LinkRecord(url=url, url_hash=url_hash, source_file="manual"))
        else:
            context.log.debug(f"Skipping {url} - summary already exists")

    for url in monitoring_links:
        if url in seen_urls:
            continue
        seen_urls.add(url)

        url_hash = compute_url_hash(url)
        summary_file = summaries_dir / f"{url_hash}.json"

        if not summary_file.exists():
            unprocessed_links.append(
                LinkRecord(url=url, url_hash=url_hash, source_file="monitoring")
            )
        else:
            context.log.debug(f"Skipping {url} - summary already exists")

    context.log.info(f"Found {len(unprocessed_links)} unprocessed links")

    # Log metadata
    context.add_output_metadata(
        {
            "total_links": len(manual_links) + len(monitoring_links),
            "manual_links": len(manual_links),
            "monitoring_links": len(monitoring_links),
            "unprocessed_links": len(unprocessed_links),
        }
    )

    return unprocessed_links

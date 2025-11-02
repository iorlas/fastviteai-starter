import hashlib
from pathlib import Path

import structlog
from dagster import AssetExecutionContext, Field, asset

from dagster_project.ops.watchers import RSSWatcher, RSSWatcherError

logger = structlog.get_logger()


def compute_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


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


@asset(
    io_manager_key="bronze_io_manager",
    config_schema={
        "source_filter": Field(str, default_value="both", is_required=False),
        "project_root": Field(str, is_required=False),
    },
    compute_kind="python",
    group_name="bronze_layer",
    tags={"layer": "bronze", "source": "ingestion"},
)
def bronze_raw_links(context: AssetExecutionContext) -> list:
    source_filter = context.op_config.get("source_filter", "both")

    project_root_str = context.op_config.get("project_root")
    if project_root_str:
        project_root = Path(project_root_str)
    else:
        project_root = Path(__file__).parent.parent.parent
    manual_file = project_root / "manual_links.txt"
    monitoring_file = project_root / "monitoring_list.txt"
    summaries_dir = project_root / "artifacts" / "summaries"

    summaries_dir.mkdir(parents=True, exist_ok=True)

    manual_links = []
    monitoring_links = []

    if source_filter in ("manual", "both"):
        manual_links = read_links_from_file(manual_file)
        logger.info("bronze_layer.raw_links.manual", count=len(manual_links))

    if source_filter in ("monitoring", "both"):
        monitoring_urls = read_links_from_file(monitoring_file)
        logger.info("bronze_layer.raw_links.monitoring_urls", count=len(monitoring_urls))

        watcher = RSSWatcher()
        for url in monitoring_urls:
            is_rss_feed = any(
                pattern in url.lower()
                for pattern in [".xml", ".rss", "/feed", "/rss", "feeds/", "atom.xml"]
            )

            if is_rss_feed:
                logger.info("bronze_layer.raw_links.rss_feed_detected", url=url)
                try:
                    discovered_links = watcher.fetch_links(url)
                    logger.info(
                        "bronze_layer.raw_links.rss_discovered",
                        url=url,
                        discovered_count=len(discovered_links),
                    )
                    monitoring_links.extend(discovered_links)
                except RSSWatcherError as e:
                    logger.warning("bronze_layer.raw_links.rss_fetch_failed", url=url, error=str(e))
            else:
                monitoring_links.append(url)

    unprocessed_links = []
    seen_urls = set()

    for url in manual_links:
        if url in seen_urls:
            continue
        seen_urls.add(url)

        url_hash = compute_url_hash(url)
        summary_file = summaries_dir / f"{url_hash}.json"

        if not summary_file.exists():
            unprocessed_links.append(url)
        else:
            logger.debug("bronze_layer.raw_links.skip_processed", url=url)

    for url in monitoring_links:
        if url in seen_urls:
            continue
        seen_urls.add(url)

        url_hash = compute_url_hash(url)
        summary_file = summaries_dir / f"{url_hash}.json"

        if not summary_file.exists():
            unprocessed_links.append(url)
        else:
            logger.debug("bronze_layer.raw_links.skip_processed", url=url)

    logger.info("bronze_layer.raw_links.complete", unprocessed_count=len(unprocessed_links))

    context.add_output_metadata(
        {
            "total_links": len(manual_links) + len(monitoring_links),
            "manual_links": len(manual_links),
            "monitoring_links": len(monitoring_links),
            "unprocessed_links": len(unprocessed_links),
        }
    )

    return unprocessed_links

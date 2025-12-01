from datetime import UTC, datetime

import structlog
from pydantic import BaseModel

from ailabbrains.config import settings
from ailabbrains.core.aggregator_resolver import resolve_url
from ailabbrains.core.content_types.youtube import YouTubeExtractor
from ailabbrains.stages.stage0_discovery import DiscoveredURL
from ailabbrains.storage import BronzeTable, exists, load, save
from ailabbrains.utils.progress_utils import progress
from ailabbrains.utils.url_utils import compute_url_hash, normalize_url

logger = structlog.get_logger()


class URLMetadata(BaseModel):
    url: str
    url_hash: str
    original_url: str | None
    content_type: str
    source: str | None
    feed_url: str | None
    discussion_links: list[dict]
    discovered_at: str | None
    classified_at: str


async def classify_urls() -> None:
    base_dir = settings.artifacts_path / "bronze"
    urls_dir = base_dir / BronzeTable.URLS

    urls_needing_classification = [
        load(base_dir, BronzeTable.URLS, url_file.stem, model=DiscoveredURL)
        for url_file in urls_dir.glob("*.json")
        if (
            not exists(base_dir, BronzeTable.URL_METADATA_HTML, url_file.stem)
            or exists(base_dir, BronzeTable.URL_METADATA_YOUTUBE, url_file.stem)
        )
    ]

    for url_hash in progress(urls_needing_classification, "URL Classification..."):
        url_data = load(base_dir, BronzeTable.URLS, url_hash, model=DiscoveredURL)
        resolved_url, discussion_link = await resolve_url(url_data.url)
        canonical_url = normalize_url(resolved_url.strip())
        canonical_hash = compute_url_hash(canonical_url)
        content_type = "youtube" if YouTubeExtractor.matches(canonical_url) else "html"

        metadata = URLMetadata(
            url=canonical_url,
            url_hash=canonical_hash,
            original_url=url_data.url if url_data.url != canonical_url else None,
            content_type=content_type,
            source=url_data.source,
            feed_url=url_data.feed_url,
            discussion_links=[discussion_link.model_dump()] if discussion_link else [],
            discovered_at=url_data.discovered_at,
            classified_at=datetime.now(UTC).isoformat(),
        )

        if content_type == "html":
            save(base_dir, BronzeTable.URL_METADATA_HTML, canonical_hash, metadata)
        else:
            save(base_dir, BronzeTable.URL_METADATA_YOUTUBE, canonical_hash, metadata)

from datetime import UTC, datetime

import structlog
from pydantic import BaseModel, Field

from ailabbrains.config import settings
from ailabbrains.storage import BronzeTable, exists, save
from ailabbrains.utils.paths import MANUAL_LINKS_FILE
from ailabbrains.utils.progress_utils import progress
from ailabbrains.utils.url_utils import compute_url_hash

logger = structlog.get_logger()


class DiscoveredURL(BaseModel):
    url: str
    source: str
    feed_url: str | None = None
    discovered_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


async def discover_manual() -> None:
    base_dir = settings.artifacts_path / "bronze"

    manual_links = []
    with open(MANUAL_LINKS_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                manual_links.append(line)

    for url in progress(manual_links, "Manual Discovery..."):
        url = url.strip()
        if not url:
            continue

        url_hash = compute_url_hash(url)

        if exists(base_dir, BronzeTable.URLS, url_hash):
            continue

        discovered = DiscoveredURL(url=url, source="manual")
        save(base_dir, BronzeTable.URLS, url_hash, discovered)

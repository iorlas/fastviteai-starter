import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from dagster_project.partitions import compute_url_hash, normalize_url
from dagster_project.utils.paths import URL_METADATA_FILE

logger = structlog.get_logger()


class URLMetadataStore:
    """Tracks canonical URLs and their discovery sources over time."""

    def __init__(self, metadata_file: Path = URL_METADATA_FILE):
        self.metadata_file = metadata_file
        self._metadata: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                self._metadata = json.load(f)
            logger.info("url_metadata.loaded", count=len(self._metadata))
        else:
            logger.info("url_metadata.initialized_empty")

    def _save(self) -> None:
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_file, "w") as f:
            json.dump(self._metadata, f, indent=2)
        logger.info("url_metadata.saved", count=len(self._metadata))

    def add_discovery(
        self,
        canonical_url: str,
        source: str,
        source_metadata: dict[str, Any],
    ) -> str:
        """Add a new discovery of a URL from a source.

        Args:
            canonical_url: Normalized canonical URL
            source: Source type (rss, hn, reddit, manual)
            source_metadata: Source-specific metadata (feed_url, post_id, etc)

        Returns:
            url_hash: The hash of the canonical URL (partition key)
        """
        canonical_url = normalize_url(canonical_url)
        url_hash = compute_url_hash(canonical_url)

        if url_hash not in self._metadata:
            self._metadata[url_hash] = {
                "canonical_url": canonical_url,
                "url_hash": url_hash,
                "sources": defaultdict(list),
                "first_discovered": datetime.now(UTC).isoformat(),
                "last_discovered": datetime.now(UTC).isoformat(),
            }
            logger.info(
                "url_metadata.new_url",
                url_hash=url_hash,
                canonical_url=canonical_url,
                source=source,
            )
        else:
            self._metadata[url_hash]["last_discovered"] = datetime.now(UTC).isoformat()
            logger.debug(
                "url_metadata.existing_url",
                url_hash=url_hash,
                canonical_url=canonical_url,
                source=source,
            )

        # Convert defaultdict to dict for existing entries
        if not isinstance(self._metadata[url_hash]["sources"], defaultdict):
            self._metadata[url_hash]["sources"] = defaultdict(list, self._metadata[url_hash]["sources"])

        # Add this discovery
        discovery = {
            **source_metadata,
            "discovered_at": datetime.now(UTC).isoformat(),
        }
        self._metadata[url_hash]["sources"][source].append(discovery)

        self._save()
        return url_hash

    def get_metadata(self, url_hash: str) -> dict[str, Any] | None:
        """Get metadata for a URL hash."""
        return self._metadata.get(url_hash)

    def get_all_url_hashes(self) -> list[str]:
        """Get all known URL hashes."""
        return list(self._metadata.keys())

    def get_urls_by_source(self, source: str) -> list[str]:
        """Get all URL hashes discovered by a specific source."""
        return [url_hash for url_hash, metadata in self._metadata.items() if source in metadata["sources"]]

    def get_unprocessed_urls(self, processed_dir: Path) -> list[str]:
        """Get URL hashes that don't have files in the processed directory."""
        unprocessed = []
        for url_hash in self._metadata.keys():
            if not (processed_dir / f"{url_hash}.json").exists():
                unprocessed.append(url_hash)
        return unprocessed

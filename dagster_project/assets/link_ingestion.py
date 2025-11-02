"""Legacy compatibility module for backward compatibility.

This module exists only to support existing assets that haven't been migrated
to the bronze layer yet. New code should not import from this module.

TODO: Remove this file once all assets are migrated to medallion architecture.
"""

from typing import NamedTuple

from dagster_project.assets.bronze_raw_links import (
    bronze_raw_links as link_ingestion_asset,
)
from dagster_project.assets.bronze_raw_links import (
    compute_url_hash,
)

__all__ = ["LinkRecord", "link_ingestion_asset", "compute_url_hash"]


class LinkRecord(NamedTuple):
    """Legacy link record format.

    Deprecated: Use bronze_raw_links asset which returns plain list of URLs.
    """

    url: str
    url_hash: str
    source: str
    watcher_type: str | None = None

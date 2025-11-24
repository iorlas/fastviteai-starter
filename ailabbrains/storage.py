"""Simplified storage layer for bronze and silver data persistence."""

import json
from enum import Enum
from pathlib import Path


class BronzeTable(str, Enum):
    """Bronze layer tables (immutable data)."""

    HTML = "html"
    YOUTUBE_DOWNLOADS = "youtube_downloads"
    DISCUSSIONS = "discussions"


class SilverTable(str, Enum):
    """Silver layer tables (regenerable data)."""

    ARTICLE_SUMMARIES = "article_summaries"
    DISCUSSION_SUMMARIES = "discussion_summaries"
    SUMMARIES = "summaries"


def get_path(
    base_dir: Path,
    partition: BronzeTable | SilverTable,
    id: str,
    sub_partition: str | None = None,
    extension: str = ".json",
    create_dirs: bool = True,
) -> Path:
    """Get path for data file with optional sub-partitioning."""
    filename = f"{id}{extension}"
    if sub_partition:
        path = base_dir / partition / sub_partition / filename
    else:
        path = base_dir / partition / filename

    if create_dirs:
        path.parent.mkdir(parents=True, exist_ok=True)

    return path


def save(
    base_dir: Path,
    partition: BronzeTable | SilverTable,
    id: str,
    data: dict,
    sub_partition: str | None = None,
) -> None:
    """Save data to JSON file."""
    path = get_path(base_dir, partition, id, sub_partition)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def load(
    base_dir: Path,
    partition: BronzeTable | SilverTable,
    id: str,
    sub_partition: str | None = None,
) -> dict:
    """Load data from JSON file."""
    path = get_path(base_dir, partition, id, sub_partition)
    return json.loads(path.read_text())


def exists(
    base_dir: Path,
    partition: BronzeTable | SilverTable,
    id: str,
    sub_partition: str | None = None,
) -> bool:
    """Check if data file exists."""
    path = get_path(base_dir, partition, id, sub_partition, create_dirs=False)
    return path.exists()

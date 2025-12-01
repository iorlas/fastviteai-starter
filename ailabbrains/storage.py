"""Simplified storage layer for bronze and silver data persistence."""

import json
from enum import Enum
from pathlib import Path
from typing import overload

from pydantic import BaseModel


class BronzeTable(str, Enum):
    """Bronze layer tables (immutable data)."""

    URLS = "urls"
    URL_METADATA = "url_metadata"
    URL_METADATA_HTML = "url_metadata_html"
    URL_METADATA_YOUTUBE = "url_metadata_youtube"
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
    data: dict | BaseModel,
    sub_partition: str | None = None,
) -> None:
    """Save data to JSON file."""
    path = get_path(base_dir, partition, id, sub_partition)
    path.parent.mkdir(parents=True, exist_ok=True)
    json_data = data.model_dump() if isinstance(data, BaseModel) else data
    path.write_text(json.dumps(json_data, indent=2, default=str))


@overload
def load[T: BaseModel](
    base_dir: Path,
    partition: BronzeTable | SilverTable,
    id: str,
    sub_partition: str | None = None,
    *,
    model: type[T],
) -> T: ...


@overload
def load(
    base_dir: Path,
    partition: BronzeTable | SilverTable,
    id: str,
    sub_partition: str | None = None,
    *,
    model: None = None,
) -> dict: ...


def load[T: BaseModel](
    base_dir: Path,
    partition: BronzeTable | SilverTable,
    id: str,
    sub_partition: str | None = None,
    *,
    model: type[T] | None = None,
) -> dict | T:
    """Load data from JSON file, optionally parsing into a Pydantic model."""
    path = get_path(base_dir, partition, id, sub_partition)
    data = json.loads(path.read_text())
    return model.model_validate(data) if model else data


def exists(
    base_dir: Path,
    partition: BronzeTable | SilverTable,
    id: str,
    sub_partition: str | None = None,
) -> bool:
    """Check if data file exists."""
    path = get_path(base_dir, partition, id, sub_partition, create_dirs=False)
    return path.exists()

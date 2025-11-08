import json
from pathlib import Path

from dagster_project.core.discussions.hn_models import HNStoryFull
from dagster_project.core.discussions.lobsters_models import LobstersStoryFull
from dagster_project.core.discussions.shared_models import DiscussionMetadata
from dagster_project.core.summary.summarizer import SummaryInput
from dagster_project.utils.tables import BronzeTable
from dagster_project.utils.url_utils import compute_url_hash


def compile_summary_input(url: str, artifacts_base_path: str) -> SummaryInput:
    """
    Compile a SummaryInput by fetching all necessary data from bronze artifacts.

    Args:
        url: The canonical URL to compile data for
        artifacts_base_path: Path to artifacts directory (e.g., "/path/to/artifacts/bronze")

    Returns:
        SummaryInput with content, title, discussions assembled from bronze layer

    Raises:
        ValueError: If bronze content doesn't exist or extraction failed
    """
    url_hash = compute_url_hash(url)
    base_path = Path(artifacts_base_path)

    extracted_content = _load_bronze_content(base_path, url_hash, url)

    if not extracted_content.get("success"):
        error_msg = extracted_content.get("error", "Content extraction failed")
        raise ValueError(f"Extraction failed for {url}: {error_msg}")

    title = extracted_content.get("title", url)
    content = extracted_content.get("content", "")
    content_type = extracted_content.get("content_type", "unknown")

    discussions_data = _load_discussions(base_path, url_hash)

    return SummaryInput(
        content=content,
        title=title,
        content_type=content_type,
        url=url,
        discussions=discussions_data,
    )


def _load_bronze_content(base_path: Path, url_hash: str, url: str) -> dict:
    """Try loading from both raw_html and raw_youtube partitions."""
    for partition in [BronzeTable.RAW_HTML, BronzeTable.RAW_YOUTUBE]:
        file_path = base_path / partition / f"{url_hash}.json"
        if file_path.exists():
            return json.loads(file_path.read_text())

    raise ValueError(f"No bronze content found for {url} (hash: {url_hash})")


def _load_discussions(base_path: Path, url_hash: str) -> list[dict] | None:
    """Load discussion metadata and stories if available."""
    metadata_path = base_path / BronzeTable.DISCUSSIONS / url_hash / "metadata.json"

    if not metadata_path.exists():
        return None

    try:
        metadata_dict = json.loads(metadata_path.read_text())
        metadata = DiscussionMetadata(**metadata_dict)

        stories = []

        for story_id in metadata.hn_story_ids:
            story_path = base_path / BronzeTable.DISCUSSIONS / url_hash / f"{story_id}.json"
            story_data = json.loads(story_path.read_text())
            stories.append(HNStoryFull(**story_data))

        for story_id in metadata.lobsters_story_ids:
            story_path = base_path / BronzeTable.DISCUSSIONS / url_hash / f"{story_id}.json"
            story_data = json.loads(story_path.read_text())
            stories.append(LobstersStoryFull(**story_data))

        return [s.model_dump() for s in stories]

    except Exception as e:
        raise ValueError(f"Failed to load discussions for hash {url_hash}: {e}") from e

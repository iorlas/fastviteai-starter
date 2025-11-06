import os
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).parent.parent.parent))

BRONZE_RAW_HTML_DIR = PROJECT_ROOT / "artifacts" / "bronze" / "raw_html"
BRONZE_RAW_LINKS_DIR = PROJECT_ROOT / "artifacts" / "bronze" / "raw_links"
BRONZE_URL_MAPPING_DIR = PROJECT_ROOT / "artifacts" / "bronze" / "url_mapping"
BRONZE_DISCUSSIONS_DIR = PROJECT_ROOT / "artifacts" / "bronze" / "discussions"
SILVER_EXTRACTED_CONTENT_DIR = PROJECT_ROOT / "artifacts" / "silver" / "extracted_content"
SILVER_SUMMARIES_DIR = PROJECT_ROOT / "artifacts" / "silver" / "summaries"
SILVER_DISCUSSIONS_DIR = PROJECT_ROOT / "artifacts" / "silver" / "silver_discussions"
ARTIFACTS_HTML_DIR = PROJECT_ROOT / "artifacts" / "html"
ARTIFACTS_VIDEOS_DIR = PROJECT_ROOT / "artifacts" / "videos"
MANUAL_LINKS_FILE = PROJECT_ROOT / "manual_links.txt"
MONITORING_LINKS_FILE = PROJECT_ROOT / "monitoring_list.txt"


def get_bronze_story_path(url_hash: str, story_id: str | int) -> Path:
    """Get path to bronze discussion story file."""
    return BRONZE_DISCUSSIONS_DIR / url_hash / f"{story_id}.json"


def get_bronze_metadata_path(url_hash: str) -> Path:
    """Get path to bronze discussion metadata file."""
    return BRONZE_DISCUSSIONS_DIR / url_hash / "metadata.json"

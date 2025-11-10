from pathlib import Path

from dagster_project.config import settings

ARTIFACTS_PATH = settings.artifacts_path

MANUAL_LINKS_FILE = ARTIFACTS_PATH / "inputs" / "manual_links.txt"
MONITORING_LINKS_FILE = ARTIFACTS_PATH / "inputs" / "monitoring_list.txt"


def get_bronze_path() -> Path:
    return ARTIFACTS_PATH / "bronze"


def get_silver_path() -> Path:
    return ARTIFACTS_PATH / "silver"


def get_cache_path() -> Path:
    return ARTIFACTS_PATH / "cache"


def get_article_summary_path(url_hash: str) -> Path:
    return ARTIFACTS_PATH / "silver" / "article_summaries" / f"{url_hash}.json"


def get_discussion_summary_dir(url_hash: str) -> Path:
    return ARTIFACTS_PATH / "silver" / "discussion_summaries" / url_hash


def get_discussion_summary_path(url_hash: str, platform: str, discussion_id: str) -> Path:
    return get_discussion_summary_dir(url_hash) / f"{platform}_{discussion_id}.json"

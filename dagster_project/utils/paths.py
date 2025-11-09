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

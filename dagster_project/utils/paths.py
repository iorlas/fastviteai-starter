from pathlib import Path

from dagster_project.config import settings

PROJECT_ROOT = settings.project_root

MANUAL_LINKS_FILE = PROJECT_ROOT / "manual_links.txt"
MONITORING_LINKS_FILE = PROJECT_ROOT / "monitoring_list.txt"


def get_bronze_path() -> Path:
    return PROJECT_ROOT / "artifacts" / "bronze"


def get_silver_path() -> Path:
    return PROJECT_ROOT / "artifacts" / "silver"

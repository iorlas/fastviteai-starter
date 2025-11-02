from dagster_project.assets.bronze_raw_html_partitioned import bronze_raw_html
from dagster_project.assets.discovered_urls import discovered_urls
from dagster_project.assets.silver_extracted_content_partitioned import (
    silver_extracted_content,
)
from dagster_project.assets.silver_summary_partitioned import silver_summary

__all__ = [
    "discovered_urls",
    "bronze_raw_html",
    "silver_extracted_content",
    "silver_summary",
]

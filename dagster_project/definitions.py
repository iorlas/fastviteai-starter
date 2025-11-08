from dagster import Definitions

from dagster_project.assets import (
    bronze_discussions,
    bronze_html,
    bronze_youtube,
    discovered_urls,
    silver_summary,
)
from dagster_project.jobs import manual_urls_pipeline, watchers_pipeline
from dagster_project.resources.storage import Storage
from dagster_project.resources.summary_generator_resource import summary_generator_resource
from dagster_project.schedules import monitoring_schedule

all_assets = [
    discovered_urls,
    bronze_html,
    bronze_youtube,
    bronze_discussions,
    silver_summary,
]

defs = Definitions(
    assets=all_assets,
    jobs=[
        manual_urls_pipeline,
        watchers_pipeline,
    ],
    schedules=[
        monitoring_schedule,
    ],
    resources={
        "summary_generator": summary_generator_resource,
        "bronze_storage": Storage(base_dir="artifacts/bronze"),
        "silver_storage": Storage(base_dir="artifacts/silver"),
    },
)

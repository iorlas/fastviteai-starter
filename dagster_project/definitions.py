from dagster import Definitions

from dagster_project.assets import (
    bronze_raw_html,
    discovered_urls,
    silver_extracted_content,
    silver_summary,
)
from dagster_project.jobs import (
    discover_and_process_job,
    discovery_only_job,
    process_partitions_job,
)
from dagster_project.resources import openai_resource
from dagster_project.resources.io_managers import BronzeIOManager, SilverIOManager
from dagster_project.schedules import monitoring_schedule

all_assets = [
    discovered_urls,
    bronze_raw_html,
    silver_extracted_content,
    silver_summary,
]

defs = Definitions(
    assets=all_assets,
    jobs=[
        discover_and_process_job,
        process_partitions_job,
        discovery_only_job,
    ],
    schedules=[
        monitoring_schedule,
    ],
    resources={
        "openai": openai_resource,
        "bronze_io_manager": BronzeIOManager(),
        "silver_io_manager": SilverIOManager(),
    },
)

from dagster import Definitions

from dagster_project.assets import (
    bronze_raw_html,
    discovered_urls,
    silver_extracted_content,
    silver_summary,
)
from dagster_project.jobs import (
    discovery_only_job,
    process_partitions_job,
)
from dagster_project.resources.io_managers import BronzeIOManager, SilverIOManager
from dagster_project.resources.summary_generator_resource import summary_generator_resource
from dagster_project.schedules import monitoring_schedule
from dagster_project.sensors import discover_and_process_sensor

all_assets = [
    discovered_urls,
    bronze_raw_html,
    silver_extracted_content,
    silver_summary,
]

defs = Definitions(
    assets=all_assets,
    jobs=[
        discovery_only_job,
        process_partitions_job,
    ],
    schedules=[
        monitoring_schedule,
    ],
    sensors=[
        discover_and_process_sensor,
    ],
    resources={
        "summary_generator": summary_generator_resource,
        "bronze_io_manager": BronzeIOManager(),
        "silver_io_manager": SilverIOManager(),
    },
)

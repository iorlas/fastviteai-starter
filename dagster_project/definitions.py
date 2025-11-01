from dagster import Definitions, load_assets_from_modules

from dagster_project import assets  # noqa: TID252
from dagster_project.jobs import manual_pipeline_job, monitoring_pipeline_job
from dagster_project.resources import openai_resource
from dagster_project.schedules import monitoring_schedule

all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
    jobs=[
        manual_pipeline_job,
        monitoring_pipeline_job,
    ],
    schedules=[
        monitoring_schedule,
    ],
    resources={
        "openai": openai_resource,
    },
)

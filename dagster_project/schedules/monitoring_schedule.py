from dagster import ScheduleDefinition

from dagster_project.jobs.partitioned_pipeline import discovery_only_job

monitoring_schedule = ScheduleDefinition(
    name="monitoring_schedule",
    cron_schedule="0 */6 * * *",
    job=discovery_only_job,
    description="Discover URLs every 6 hours (sensor auto-processes new URLs)",
)

from dagster import ScheduleDefinition

from dagster_project.jobs.partitioned_pipeline import discover_and_process_job

monitoring_schedule = ScheduleDefinition(
    name="monitoring_schedule",
    cron_schedule="0 */6 * * *",
    job=discover_and_process_job,
    description="Discover and process URLs every 6 hours (all sources: RSS, manual, monitoring)",
)
